from typing import AsyncContextManager, Callable, Coroutine, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from models import User


def new_telegram_application(
    token: str, session_factory: Callable[[], AsyncContextManager[AsyncSession]]
) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_factory(session_factory)))

    return application


def start_factory(
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[None, None, None]]:

    async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message
        assert update.message.from_user
        user_id = update.message.from_user.id

        async with session_factory() as session:
            statement = select(User).where(
                User.integrations["telegram"]["user_id"].astext == str(user_id)
            )
            user = cast(User, await session.scalar(statement))
            if not user:
                await session.commit()
                return
            await update.message.reply_text(user.email)
            await session.commit()

    return start
