from datetime import timedelta

from apscheduler.schedulers.base import BaseScheduler
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.base import BaseTool, BaseToolkit
from pydantic import BaseModel
from pydantic.fields import PrivateAttr

from tools.base import UserAwareBaseTool


class SchedulerToolkit(BaseToolkit):
    _scheduler: BaseScheduler = PrivateAttr()

    def __init__(self, scheduler: BaseScheduler):
        super().__init__()
        self._scheduler = scheduler

    def get_tools(self) -> list[BaseTool]:
        create_tool = SchedulerCreateTool()
        create_tool._scheduler = self._scheduler
        tools: list[BaseTool] = [create_tool]
        return tools


class SchedulerCreateInput(BaseModel):
    code: str
    interval_seconds: int


def run_job(code: str, user_id: str):
    code = """
from tools import create_tools

tools = create_tools()
tools["user_id"] = "{}"
"""
    exec(code)


class SchedulerCreateTool(UserAwareBaseTool):
    name: str = "scheduler_create"
    description: str = "Create a new scheduler"
    args_schema: type = SchedulerCreateInput

    _scheduler: BaseScheduler = PrivateAttr()

    async def _arun(self, code: str, interval_seconds: int, config: RunnableConfig):
        self._scheduler.add_job(
            func=run_job,
            trigger="interval",
            args=[code, self._get_user_id(config)],
            seconds=interval_seconds,
        )
