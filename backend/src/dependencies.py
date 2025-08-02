import os
from contextlib import asynccontextmanager
from typing import AsyncContextManager, AsyncIterator, Callable

from apscheduler.executors.pool import ThreadPoolExecutor  # type: ignore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore  # type: ignore
from apscheduler.schedulers.background import (  # type: ignore
    BackgroundScheduler,
    BaseScheduler,
)
from graphiti_core import Graphiti
from langchain.chat_models import init_chat_model
from langchain.globals import set_debug
from langgraph.graph.state import CompiledStateGraph
from neo4j import GraphDatabase
from openai import OpenAI
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from agent.graph import create_graph
from agent.postgres_saver import LazyAsyncPostgresSaver
from jwt_token import TokenManager, get_current_user_factory
from neo4j_client import Neo4jClient


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
    executors = {"default": ThreadPoolExecutor(5)}
    job_defaults = {"max_instances": 1, "coalesce": True, "misfire_grace_time": None}
    return BackgroundScheduler(
        jobstores=jobstores, executors=executors, job_defaults=job_defaults
    )


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


def new_graph(
    checkpointer: LazyAsyncPostgresSaver,
    graphiti: Graphiti,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
) -> CompiledStateGraph:
    return create_graph(
        checkpointer=checkpointer,
        llm=init_chat_model("gpt-3.5-turbo"),
        session_factory=session_factory,
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        google_search_api_key=os.environ["GOOGLE_SEARCH_API_KEY"],
        google_search_engine_id=os.environ["GOOGLE_SEARCH_ENGINE_ID"],
        graphiti=graphiti,
    )


######### Telegram ########

TELEGRAM_APPLICATION_TOKEN = os.environ["TELEGRAM_APPLICATION_TOKEN"]


def get_telegram_application_token() -> str:
    return TELEGRAM_APPLICATION_TOKEN


######## Graphiti ########


def new_graphiti() -> Graphiti:
    return Graphiti(
        os.environ["NEO4J_URI"],
        os.environ["NEO4J_USERNAME"],
        os.environ["NEO4J_PASSWORD"],
    )
