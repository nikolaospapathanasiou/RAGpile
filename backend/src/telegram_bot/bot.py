from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


def new_telegram_bot(token: str) -> Application:
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))

    return application


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat.id

    update.message.reply_text("Hello, World!")
