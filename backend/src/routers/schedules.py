import logging
from datetime import datetime
from typing import Annotated

from apscheduler.job import Job
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_scheduler, get_session
from models import Schedule, User

schedules_router = APIRouter()
logger = logging.getLogger(__name__)


class ResponseSchedule(BaseModel):
    id: str
    user_id: str
    code: str
    interval_seconds: int
    next_run_time: datetime | None

    @classmethod
    def from_job(cls, job: Job, user_id: str) -> "ResponseSchedule":
        return cls(
            id=job.id,
            user_id=user_id,
            code=job.args[0],
            interval_seconds=job.trigger.interval_length,
            next_run_time=job.next_run_time,
        )


@schedules_router.get("/schedules")
async def get_schedules(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)],
) -> list[ResponseSchedule]:
    query = await session.execute(
        select(Schedule).where(Schedule.user_id == current_user.id)
    )
    schedules = query.scalars().all()
    result: list[ResponseSchedule] = []
    for schedule in schedules:
        job = scheduler.get_job(schedule.id)
        if job is None:
            await session.delete(schedule)
            continue
        result.append(ResponseSchedule.from_job(job, current_user.id))
    return result


@schedules_router.put("/schedules/{schedule_id}")
async def update_schedule(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    scheduler: Annotated[BaseScheduler, Depends(get_scheduler)],
    schedule_id: str,
    in_schedule: ResponseSchedule,
) -> ResponseSchedule:
    db_schedule = await session.get(Schedule, (current_user.id, schedule_id))
    if db_schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

    job: Job | None = scheduler.get_job(schedule_id)
    if job is None:
        await session.delete(db_schedule)
        raise HTTPException(status_code=404, detail="Schedule not found")
    new_args = (in_schedule.code, job.args[1:])
    new_trigger = IntervalTrigger(seconds=in_schedule.interval_seconds)
    new_job: Job = scheduler.modify_job(schedule_id, args=new_args, trigger=new_trigger)
    return ResponseSchedule.from_job(new_job, current_user.id)
