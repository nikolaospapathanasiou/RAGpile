import asyncio
import threading
from dataclasses import dataclass

from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel
from telegram import Bot

from tools.base import AsyncBaseTool


class SchedulerCreateInput(BaseModel):
    code: str
    interval_seconds: int


@dataclass
class Schedule:
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
        Create a new scheduled job. This job will run the given code every interval_seconds seconds.
        The job has access to all the tools that are available to you.
        They are available in a python dict in the global scope, so you can access it like:
        `tools["tool_name"]`
        For example, if you want to use the tool named "google_search", you can do:
        `result = tools["google_search"].run("query")`
        You can also send message to the user by calling `send_message("message")`
    """
    args_schema: type = SchedulerCreateInput

    async def _arun(
        self, code: str, interval_seconds: int, config: RunnableConfig
    ) -> Schedule:
        job = self.dependencies.scheduler.add_job(
            func=run_job,
            trigger="interval",
            args=[code, self._get_user_id(config)],
            seconds=interval_seconds,
        )
        return Schedule(next_run_time=job.next_run_time, id=job.id)
