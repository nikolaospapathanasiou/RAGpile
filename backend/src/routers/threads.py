import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.runnables.config import RunnableConfig
from langgraph.checkpoint.base import Checkpoint
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_checkpointer, get_current_user, get_session
from models import Thread, User

threads_router = APIRouter()
logger = logging.getLogger(__name__)


class ResponseThread(BaseModel):
    id: str
    user_id: str
    created_at: datetime


@threads_router.get("/threads", response_model=list[ResponseThread])
async def get_threads(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    result = await session.execute(
        select(Thread)
        .where(Thread.user_id == current_user.id)
        .order_by(Thread.created_at.desc())
    )
    threads = result.scalars().all()

    return [
        ResponseThread(
            id=thread.id,
            user_id=thread.user_id,
            created_at=thread.created_at,
        )
        for thread in threads
    ]


@threads_router.get("/threads/{thread_id}", response_model=Checkpoint)
async def get_thread(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    checkpointer: Annotated[AsyncPostgresSaver, Depends(get_checkpointer)],
    thread_id: str,
):
    result = await session.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalars().one()
    if thread.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    checkpoint_tuple = await checkpointer.aget_tuple(
        RunnableConfig(configurable={"thread_id": thread_id})
    )
    if not checkpoint_tuple:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    return checkpoint_tuple.checkpoint
