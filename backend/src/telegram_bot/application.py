from typing import AsyncContextManager, Callable, Coroutine, cast

from langgraph.graph.graph import CompiledGraph
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler

from models import User


def new_telegram_application(
    token: str,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    graph: CompiledGraph,
) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start(session_factory)))
    application.add_handler(MessageHandler(None, echo(graph)))

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
                await session.commit()
                return
            if not update.effective_chat:
                return
            user.integrations["telegram"]["effective_chat_id"] = str(
                update.effective_chat.id
            )
            await session.execute(User.update_integrations(user))
            await update.message.reply_text(user.email)
            await session.commit()

    return _start


def echo(
    graph: CompiledGraph,
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[None, None, None]]:
    async def _echo(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message:
            return
        if not update.effective_chat:
            return
        for event in graph.stream(
            {"messages": [{"role": "user", "content": update.message.text}]},
            {"configurable": {"thread_id": update.effective_chat.id}},
        ):
            for value in event.values():
                await update.message.reply_text(value["messages"][-1].content)

    return _echo
