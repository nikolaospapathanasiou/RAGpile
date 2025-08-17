from datetime import datetime
from typing import AsyncContextManager, Callable, Coroutine, cast
from uuid import uuid4

from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler

from models import Thread, User


def new_telegram_application(
    token: str,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    graph: CompiledStateGraph,
) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start(session_factory)))
    application.add_handler(CommandHandler("clear", clear(session_factory)))
    application.add_handler(MessageHandler(None, reply(graph, session_factory)))

    return application


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
    graph: CompiledStateGraph,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
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
            thread_id = user.integrations["telegram"].get("thread_id")
            if not thread_id:
                thread_id = uuid4().hex
                session.add(
                    Thread(
                        id=thread_id,
                        user_id=user.id,
                        created_at=datetime.utcnow(),
                    )
                )
                user.integrations["telegram"]["thread_id"] = thread_id
                await session.execute(User.update_integrations(user))
        async for event in graph.astream(
            {
                "messages": [{"role": "user", "content": update.message.text}],
            },
            {"configurable": {"thread_id": thread_id, "user_id": user.id}},
        ):
            for value in event.values():
                content = value["messages"][-1].content

                if not content or value["messages"][-1].type == "tool":
                    continue

                await update.message.reply_text(
                    value["messages"][-1].content, parse_mode="HTML"
                )

    return _reply
