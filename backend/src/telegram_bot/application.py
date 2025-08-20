from datetime import datetime, timezone
from asyncio import QueueShutDown
from typing import AsyncContextManager, Callable, Coroutine, cast
from uuid import uuid4

from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler

from agent.agent import Agent
from message_queue import MessageQueue, MessageWithUserId
from models import Thread, User


class TelegramApplication(Application):
    QUEUE_HANDLE = "telegram"

    def __init__(
        self,
        queue: MessageQueue,
        application: Application,
        session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    ):
        self.application = application
        self.queue = queue
        self.queue.register(self.QUEUE_HANDLE)
        self.session_factory = session_factory

    async def send_pending_messages(self) -> None:
        while True:
            try:
                message_with_chat = await self.queue.get(self.QUEUE_HANDLE)
            except QueueShutDown:
                break
            if message_with_chat.message.type == "tool":
                continue
            async with self.session_factory() as session:
                user = cast(User, await session.get(User, message_with_chat.user_id))
                if not user:
                    raise ValueError(
                        "User could not be found when processing a message in queue. That should not have happened."
                    )
                chat_id = user.integrations["telegram"]["effective_chat_id"]
            await cast(Bot, self.application.bot).send_message(
                chat_id,
                str(message_with_chat.message.content),
                parse_mode="HTML",
            )


def new_telegram_application(
    token: str,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    agent: Agent,
    queue: MessageQueue,
) -> TelegramApplication:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start(session_factory)))
    application.add_handler(CommandHandler("clear", clear(session_factory)))
    application.add_handler(MessageHandler(None, reply(agent, session_factory, queue)))
    return TelegramApplication(queue, application, session_factory)


def start(
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[None, None, None]]:

    async def _start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        assert update.message.from_user
        user_id = update.message.from_user.id

        async with session_factory() as session:
            user = cast(
                User, await session.scalar(User.select_user_from_telegram_id(user_id))
            )
            if not user:
                return
            if not update.effective_chat:
                return
            user.integrations["telegram"]["effective_chat_id"] = str(
                update.effective_chat.id
            )
            await session.execute(User.update_integrations(user))
            await update.message.reply_text(user.email)

    return _start


def clear(
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[None, None, None]]:

    async def _clear(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        async with session_factory() as session:
            assert update.message
            assert update.message.from_user
            user = cast(
                User,
                await session.scalar(
                    User.select_user_from_telegram_id(update.message.from_user.id)
                ),
            )
            if not user:
                return
            user.integrations["telegram"]["thread_id"] = ""
            await session.execute(User.update_integrations(user))
            await session.commit()

    return _clear


def reply(
    agent: Agent,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    queue: MessageQueue,
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[None, None, None]]:
    async def _reply(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        assert update.effective_chat
        assert update.message.from_user

        user = None
        async with session_factory() as session:
            user = cast(
                User,
                await session.scalar(
                    User.select_user_from_telegram_id(update.message.from_user.id)
                ),
            )
            if not user:
                return
            session.expunge(user)
        thread_id = await agent.get_current_thread_id(user)
        async for event in agent.graph.astream(
            {
                "messages": [{"role": "user", "content": update.message.text}],
            },
            {"configurable": {"thread_id": thread_id, "user_id": user.id}},
        ):
            for value in event.values():
                content = value["messages"][-1].content

                if not content or value["messages"][-1].type == "tool":
                    continue

                await queue.put(
                    MessageWithUserId(
                        user_id=user.id,
                        message=value["messages"][-1],
                    )
                )

    return _reply
