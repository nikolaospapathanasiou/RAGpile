import asyncio
import threading
from dataclasses import dataclass
from typing import Any, AsyncContextManager, Callable, cast
from uuid import uuid4

from apscheduler.job import Job
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent import Agent
from models import Schedule, User
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


def run_job(code: str, user_id: str, job_id: str, state: dict[str, Any] = {}) -> None:
    loop = asyncio.get_event_loop()

    tools: dict[str, AsyncBaseTool] = local.tools
    for tool in tools.values():
        tool.bind_user_id(user_id)

    agent: Agent = local.agent
    llm: BaseChatModel = local.llm
    session_factory: Callable[[], AsyncContextManager[AsyncSession]] = (
        local.session_factory
    )
    scheduler: BaseScheduler = local.scheduler
    job: Job = cast(Job, scheduler.get_job(job_id))

    async def get_user(user_id: str) -> User:
        async with session_factory() as session:
            user = await session.get(User, user_id)
            assert user
            session.expunge(user)
            return user

    user = loop.run_until_complete(get_user(user_id))

    def send_message(text: str) -> None:
        async def _send_message(text: str) -> None:
            await agent.send_message(
                [
                    SystemMessage(
                        content=f"The following message is message sent form job {job.name}"
                    ),
                    AIMessage(content=text),
                ],
                user,
            )

        loop.run_until_complete(_send_message(text))

    def invoke_llm(text: str) -> str:
        system_message = SystemMessage(
            content="""
            You are an assistant, this is a message that is requested in a cron like job.
            Try to keep them short, because those messages will probably be sent to the user
            through telegram.
            """
        )
        user_messgae = HumanMessage(content=text)
        message = llm.invoke([system_message, user_messgae])
        return str(message.content)

    exec(
        code,
        None,
        {
            "tools": local.tools,
            "user_id": user_id,
            "send_message": send_message,
            "invoke_llm": invoke_llm,
            "state": state,
        },
    )
    scheduler.modify_job(job_id, kwargs={**job.kwargs, "state": state})


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
        The input is a dict with the keys named as described in the tools.
        For example, if you want to use the tool named "google_search", you can do:
        `result = tools["google_search"].run({"query": "What are the latest news?"})`
        If you want to call a tool without any input, you still need to pass in an empty dict.
        The results are python dataclasses or a list of dataclasses, the attributes can be accessed with the dot notation, for example:
        `result.title`
        `result[0].link`
        If you want to invoke an llm in order to parse some data and create a message for the user you can do:
        `result = invoke_llm("Can you summarize the latest news?" + str(result))`.
        Always use invoke_llm if you are requested to process data and create a message for the user.
        DO NOT use non existing tools.
        DO NOT use result['items'] for the result of a tool, the return value is either a list or a dataclass.
        You can also send message to the user by calling `send_message("message")`
        You can remember things about the execution of the job by storing them in a variable named `state`.
        For example, lets say you want to store the results of a tool, you can do:
        ```
        previous_results = state.get("previous_results", [])
        results = tools["google_search"].run({"query": "What are the latest news?"})
        state["previous_results"] = results
        # here you can use both last run and current run, while also preparing for the next
        ```
        when you plan to use this, always ask first if this is what the user wants by showing the code and waiting for a confirmation.
    """
    args_schema: type = SchedulerCreateInput

    async def _arun(
        self, name: str, code: str, crontab: str, config: RunnableConfig
    ) -> SchedulerCreate:
        job_id = uuid4().hex
        job = self.dependencies.scheduler.add_job(
            id=job_id,
            name=name,
            func=run_job,
            trigger=CronTrigger.from_crontab(crontab),
            kwargs={
                "code": code,
                "user_id": self._get_user_id(config),
                "job_id": job_id,
            },
        )
        async with self.dependencies.session_factory() as session:
            schedule = Schedule(user_id=self._get_user_id(config), id=job.id)
            session.add(schedule)
            await session.commit()
        return SchedulerCreate(next_run_time=job.next_run_time, id=job.id)
