import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager
from typing import Annotated, Optional

import debugpy  # type: ignore
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (
    CHECKPOINTER,
    ENGINE,
    MESSAGE_QUEUE,
    TELEGRAM_APPLICATION_TOKEN,
    create_engine,
    create_session_factory,
    get_scheduler,
    get_session,
    new_checkpointer,
    new_agent,
    new_graphiti,
    new_tools,
)
from log import init_logger
from models import User
from routers.auth import auth_router
from routers.openai_wrapper import openai_router
from routers.schedules import schedules_router
from routers.threads import threads_router
from telegram_bot.application import new_telegram_application

init_logger()
logger = logging.getLogger(__name__)


def run_telegram_application(stop_event: threading.Event):
    async def _run() -> None:
        graphiti = new_graphiti()
        await graphiti.build_indices_and_constraints()
        session_factory = asynccontextmanager(create_session_factory(create_engine()))
        checkpointer = new_checkpointer()
        await checkpointer.connect()
        telegram_application = new_telegram_application(
            TELEGRAM_APPLICATION_TOKEN,
            session_factory,
            new_agent(
                checkpointer=checkpointer,
                tools=new_tools(graphiti=graphiti, session_factory=session_factory),
                session_factory=session_factory,
                queue=MESSAGE_QUEUE,
            ),
            MESSAGE_QUEUE,
        )
        application = telegram_application.application

        await application.initialize()
        assert application.updater is not None
        await application.updater.start_polling(poll_interval=10.0, timeout=30)
        await application.start()

        while not stop_event.is_set():
            await telegram_application.send_pending_messages()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await checkpointer.close()
        await graphiti.close()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_run())


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting up checkpointer")
    await CHECKPOINTER.connect()
    await CHECKPOINTER.setup()
    logger.info("Starting up telegram application")
    stop_event = threading.Event()
    telegram_thread = threading.Thread(
        target=run_telegram_application, args=(stop_event,)
    )
    telegram_thread.start()
    if os.environ.get("ENABLE_DEBUGPY") == "1":
        debug_port = 5678
        print(f"Debugger listening on port {debug_port} ...")
        debugpy.listen(("0.0.0.0", debug_port))
    logger.info("Starting up scheduler")
    scheduler = get_scheduler()
    scheduler.start()
    yield
    logger.info("Shutting down telegram application")
    await MESSAGE_QUEUE.shutdown()
    stop_event.set()
    telegram_thread.join()
    logger.info("Shutting down scheduler")
    scheduler.shutdown()
    logger.info("Shutting down postgres engine")
    await ENGINE.dispose()
    logger.info("Shutting down checkpointer")
    await CHECKPOINTER.close()
    logger.info("Shutting down graphiti")


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/ragpile/api")
app.include_router(openai_router, prefix="/ragpile/api")
app.include_router(threads_router, prefix="/ragpile/api")
app.include_router(schedules_router, prefix="/ragpile/api")


class Webhook(BaseModel):
    action: str
    message: str
    user: Optional[str]


class WebhookUser(BaseModel):
    id: str
    name: str
    email: str
    profile_image_url: str


@app.post("/webhook")
async def webhook(db: Annotated[AsyncSession, Depends(get_session)], request: Webhook):
    # {
    #   "action": "signup",
    #   "message": "New user signed up: Stavros",
    #   "user": "{
    #       \"id\":\"be36236b-18b4-41f9-b717-2a64fdd654b9\",
    #       \"name\":\"Stavros\",
    #       \"email\":\"stavros.champilomatis@gmail.com\",
    #       \"role\":\"pending\",
    #       \"profile_image_url\":\"...",
    #       \"last_active_at\":1744376774,
    #       \"updated_at\":1744376774,
    #       \"created_at\":1744376774,
    #       \"oauth_sub\":\"google@100223762578536717199\"
    #   }"
    if request.action != "signup":
        return {"status": "ok"}
    if not request.user:
        logger.error("No user in webhook")
        raise HTTPException(status_code=400, detail="No user in webhook")

    webhook_user = WebhookUser.parse_raw(request.user)
    user = User(id=webhook_user.id, name=webhook_user.name, email=webhook_user.email)
    db.add(user)
    await db.commit()
    return {"status": "ok"}
