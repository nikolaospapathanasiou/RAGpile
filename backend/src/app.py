import logging
import multiprocessing
import os
from contextlib import asynccontextmanager
from typing import Annotated, Optional, cast

import debugpy  # type: ignore
from fastapi import Depends, FastAPI, HTTPException
from psycopg_pool import ConnectionPool
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import auth_router
from dependencies import (
    CHECKPOINTER,
    ENGINE,
    get_scheduler,
    get_session,
    get_telegram_application,
)
from log import init_logger
from models import User
from openai_wrapper import openai_router

init_logger()
logger = logging.getLogger(__name__)


def run_application():
    logger.info("Starting up telegram application")
    application = get_telegram_application()
    application.run_polling(poll_interval=10.0, timeout=30)


@asynccontextmanager
async def lifespan(_: FastAPI):
    process = multiprocessing.Process(target=run_application)
    process.start()
    if os.environ.get("ENABLE_DEBUGPY") == "1":
        debug_port = 5678
        print(f"Debugger listening on port {debug_port} ...")
        debugpy.listen(("0.0.0.0", debug_port))
    logger.info("Starting up checkpointer")
    cast(ConnectionPool, CHECKPOINTER.conn).open()
    CHECKPOINTER.setup()
    logger.info("Starting up scheduler")
    scheduler = get_scheduler()
    scheduler.start()
    yield
    logger.info("Shutting down telegram application")
    process.terminate()
    process.join()
    process.close()
    logger.info("Shutting down scheduler")
    scheduler.shutdown()
    logger.info("Shutting down postgres engine")
    await ENGINE.dispose()
    logger.info("Shutting down checkpointer")
    CHECKPOINTER.conn.close()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router, prefix="/ragpile/api")
app.include_router(openai_router, prefix="/ragpile/api")


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
