import asyncio
import threading
from dataclasses import dataclass

from apscheduler.triggers.cron import CronTrigger
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel
from telegram import Bot

from models import Schedule
from tools.base import AsyncBaseTool


class SchedulerCreateInput(BaseModel):
    name: str
    code: str
    crontab: str


@dataclass
class SchedulerCreate:
    next_run_time: float
    id: str


local = threading.local()


def run_job(code: str, user_id: str):
    loop = asyncio.get_event_loop()

    tools: dict[str, AsyncBaseTool] = local.tools
    for tool in tools.values():
        tool.bind_user_id(user_id)

    user = loop.run_until_complete(tools["scheduler_create"].get_user({}))
    bot: Bot = local.bot

    def send_message(text: str):
        loop.run_until_complete(
            bot.send_message(
                chat_id=user.integrations["telegram"]["effective_chat_id"], text=text
            )
        )

    exec(
        code,
        None,
        {"tools": local.tools, "user_id": user_id, "send_message": send_message},
    )


class SchedulerCreateTool(AsyncBaseTool):
    name: str = "scheduler_create"
    description: str = """
        Create a new scheduled job. This job will run the given code based on the crontab.
        Pick a descriptive name for the job.
        The code is python.
        Crontab is folllowing the standard format, for example: 10 10 * * * runs at 10:10 every day
        The job has access to all the tools that are available to you.
        They are available in a python dict in the global scope, so you can access it like:
        `tools["tool_name"]`
        For example, if you want to use the tool named "google_search", you can do:
        `result = tools["google_search"].run("What are the latest news?")`
        The results are python dataclasses or a list of dataclasses, the attributes can be accessed with the dot notation, for example:
        `result.title`
        `result[0].link`
        You can also send message to the user by calling `send_message("message")`
        when you plan to use this, always ask first if this is what the user wants.
    """
    args_schema: type = SchedulerCreateInput

    async def _arun(
        self, name: str, code: str, crontab: str, config: RunnableConfig
    ) -> SchedulerCreate:
        job = self.dependencies.scheduler.add_job(
            name=name,
            func=run_job,
            trigger=CronTrigger.from_crontab(crontab),
            args=[code, self._get_user_id(config)],
        )
        async with self.dependencies.session_factory() as session:
            schedule = Schedule(user_id=self._get_user_id(config), id=job.id)
            session.add(schedule)
            await session.commit()
        return SchedulerCreate(next_run_time=job.next_run_time, id=job.id)
