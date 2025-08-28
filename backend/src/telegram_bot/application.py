from asyncio import QueueShutDown
from dataclasses import dataclass
from typing import AsyncContextManager, Callable, Coroutine, Generator, cast

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler

from agent.agent import Agent
from message_queue import MessageQueue
from models import User


def split_message_to_chunks(message: str, chunk_size: int = 4096) -> Generator[str]:
    chunk_index = 0
    content = message
    chunk = content[0:chunk_size]
    while chunk:
        yield chunk
        chunk_index += 1
        chunk = content[chunk_index * chunk_size : (chunk_index + 1) * chunk_size]


def remove_unclosed_tags(message: str) -> str:
    @dataclass
    class Tag:
        start: int
        end: int
        name: str
        name_found: bool

    def remove_tag(m: str, tag: Tag) -> str:
        return m[: tag.start] + m[tag.end + 1 :]

    tags: list[Tag] = []
    for i, c in enumerate(message):
        if c == "<":
            tags.append(Tag(start=i, end=-1, name="", name_found=False))
            continue

        if len(tags) == 0:
            continue

        if c == ">":
            tags[-1].end = i
            tags[-1].name_found = True
            continue

        if tags[-1].name_found:
            continue

        if c == " ":
            tags[-1].name_found = True
            continue

        tags[-1].name += c

    open_tags: list[Tag] = []
    for tag in tags:
        if tag.name[0] == "/":
            if len(open_tags) == 0:
                message = remove_tag(message, tag)
                continue

            if len(open_tags) >= 1 and open_tags[-1].name == tag.name[1:]:
                open_tags.pop()
                continue

            if len(open_tags) >= 2 and open_tags[-2].name == tag.name[1:]:
                unclosed_tag = open_tags.pop()
                message = remove_tag(message, unclosed_tag)
                open_tags.pop()
                continue
            message = remove_tag(message, tag)
        else:
            open_tags.append(tag)
    for tag in open_tags:
        message = remove_tag(message, tag)
    return message


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
                message_with_user_id = await self.queue.get(self.QUEUE_HANDLE)
            except QueueShutDown:
                break
            if message_with_user_id.message.type == "tool":
                continue
            if not message_with_user_id.message.content:
                continue
            async with self.session_factory() as session:
                user = cast(User, await session.get(User, message_with_user_id.user_id))
                if not user:
                    raise ValueError(
                        "User could not be found when processing a message in queue. That should not have happened."
                    )
                chat_id = user.integrations["telegram"]["effective_chat_id"]
            for chunk in split_message_to_chunks(
                str(message_with_user_id.message.content)
            ):
                await cast(Bot, self.application.bot).send_message(
                    chat_id,
                    chunk,
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
    application.add_handler(MessageHandler(None, reply(agent, session_factory)))
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
        if not update.message.text:
            return
        await agent.send_message([HumanMessage(content=update.message.text)], user)

    return _reply
