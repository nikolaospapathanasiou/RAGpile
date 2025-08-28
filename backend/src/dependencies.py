import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Callable

from apscheduler.executors.pool import ThreadPoolExecutor  # type: ignore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore  # type: ignore
from apscheduler.schedulers.background import (  # type: ignore
    BackgroundScheduler,
    BaseScheduler,
)
from asyncpraw import Reddit
from graphiti_core import Graphiti
from langchain.chat_models import init_chat_model
from langchain.globals import set_debug
from langchain_core.tools.base import BaseTool
from langgraph.graph.state import CompiledStateGraph
from openai import OpenAI
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from telegram import Bot

from agent.agent import Agent
from agent.graph import create_agent, create_tools
from agent.postgres_saver import LazyAsyncPostgresSaver
from jwt_token import TokenManager, get_current_user_factory
from message_queue import MessageQueue
from tools.scheduler import local


######### DATABASE #########
def create_engine() -> AsyncEngine:

    url = URL.create(
        drivername="postgresql+asyncpg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host="db",
        port=5432,
        database=os.environ["POSTGRES_DB"],
    )

    return create_async_engine(url, echo=True)


ENGINE = create_engine()


def create_session_factory(
    engine: AsyncEngine,
) -> Callable[[], AsyncIterator[AsyncSession]]:
    session_maker = async_sessionmaker(bind=engine)

    async def _session_factory() -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            async with session.begin():
                yield session

    return _session_factory


get_session = create_session_factory(ENGINE)
get_session_factory = asynccontextmanager(get_session)


######## JWT ########
get_current_user = get_current_user_factory(
    TokenManager(os.environ["JWT_SECRET"]), get_session
)

###### LLMs ######
CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_openai_client() -> OpenAI:
    return CLIENT


####### APScheduler #######
def new_scheduler() -> BaseScheduler:
    url = URL.create(
        drivername="postgresql",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host="db",
        port=5432,
        database=os.environ["POSTGRES_SCHEDULER_DB"],
    )
    jobstores = {"default": SQLAlchemyJobStore(url=url)}

    job_defaults = {"max_instances": 1, "coalesce": True, "misfire_grace_time": None}
    scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults)

    def _init():
        asyncio.set_event_loop(asyncio.new_event_loop())
        session_factory = asynccontextmanager(create_session_factory(create_engine()))
        tools = new_tools(graphiti=new_graphiti(), session_factory=session_factory)

        local.tools = {tool.name: tool for tool in tools}
        local.scheduler = scheduler
        local.session_factory = session_factory
        local.agent = new_agent(
            tools=tools,
            session_factory=session_factory,
            queue=MESSAGE_QUEUE,
            checkpointer=CHECKPOINTER,
        )
        local.bot = Bot(token=get_telegram_application_token())
        local.llm = init_chat_model("gpt-4.1")

    scheduler.add_executor(
        ThreadPoolExecutor(1, pool_kwargs={"initializer": _init}), alias="default"
    )
    return scheduler


SCHEDULER = new_scheduler()


def get_scheduler() -> BaseScheduler:
    return SCHEDULER


######## Langgraph Checkpointer ########
def new_checkpointer() -> LazyAsyncPostgresSaver:
    url = URL.create(
        drivername="postgresql",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host="db",
        port=5432,
        database=os.environ["POSTGRES_CHECKPOINTER_DB"],
    )
    return LazyAsyncPostgresSaver(url.render_as_string(False))


CHECKPOINTER = new_checkpointer()


def get_checkpointer() -> LazyAsyncPostgresSaver:
    return CHECKPOINTER


######## Graphs ########

set_debug(True)


def new_tools(
    graphiti: Graphiti, session_factory: Callable[[], AsyncContextManager[AsyncSession]]
) -> list[BaseTool]:
    return create_tools(
        graphiti=graphiti,
        session_factory=session_factory,
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        google_search_api_key=os.environ["GOOGLE_SEARCH_API_KEY"],
        google_search_engine_id=os.environ["GOOGLE_SEARCH_ENGINE_ID"],
        scheduler=SCHEDULER,
        reddit_client=Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent="RAGpile",
            username=os.environ["REDDIT_USERNAME"],
            password=os.environ["REDDIT_PASSWORD"],
        ),
    )


def new_agent(
    tools: list[BaseTool],
    checkpointer: LazyAsyncPostgresSaver,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    queue: MessageQueue,
) -> Agent:
    return create_agent(
        tools=tools,
        checkpointer=checkpointer,
        llm=init_chat_model("gpt-4.1"),
        session_factory=session_factory,
        queue=queue,
    )


######### Telegram ########

TELEGRAM_APPLICATION_TOKEN = os.environ["TELEGRAM_APPLICATION_TOKEN"]


def get_telegram_application_token() -> str:
    return TELEGRAM_APPLICATION_TOKEN


MESSAGE_QUEUE = MessageQueue()
######## Graphiti ########


def new_graphiti() -> Graphiti:
    return Graphiti(
        os.environ["NEO4J_URI"],
        os.environ["NEO4J_USERNAME"],
        os.environ["NEO4J_PASSWORD"],
    )
