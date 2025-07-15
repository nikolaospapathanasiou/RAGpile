import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.executors.pool import ThreadPoolExecutor  # type: ignore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore  # type: ignore
from apscheduler.schedulers.background import (  # type: ignore
    BackgroundScheduler,
    BaseScheduler,
)
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.state import CompiledStateGraph
from neo4j import GraphDatabase
from openai import OpenAI
from psycopg import Connection
from psycopg.rows import DictRow
from psycopg_pool import ConnectionPool
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from telegram.ext import Application

from agents.email import create_graph as create_email_graph
from auth.token import TokenManager, get_current_user_factory
from neo4j_client import Neo4jClient
from telegram_bot.application import new_telegram_application


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
SESSIONFACTORY = async_sessionmaker(bind=ENGINE)


@asynccontextmanager
async def get_session_factory() -> AsyncIterator[AsyncSession]:
    async with SESSIONFACTORY() as session:
        async with session.begin():
            yield session


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SESSIONFACTORY() as session:
        async with session.begin():
            yield session


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
        database=os.environ["POSTGRES_DB"],
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
def new_checkpointer() -> PostgresSaver:
    url = URL.create(
        drivername="postgresql",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host="db",
        port=5432,
        database=os.environ["POSTGRES_DB"],
    )
    pool = ConnectionPool(
        url.render_as_string(hide_password=False),
        connection_class=Connection[DictRow],
        kwargs={"autocommit": True},
    )
    return PostgresSaver(pool)


CHECKPOINTER = new_checkpointer()

######## Graphs ########


def new_graphs() -> dict[str, CompiledStateGraph]:
    return {"email": create_email_graph(CHECKPOINTER, init_chat_model("gpt-3.5-turbo"))}


GRAPHS = new_graphs()


def get_graphs() -> dict[str, CompiledStateGraph]:
    return GRAPHS


######### Telegram ########

TELEGRAM_APPLICATION_TOKEN = os.environ["TELEGRAM_APPLICATION_TOKEN"]


def get_telegram_application_token() -> str:
    return TELEGRAM_APPLICATION_TOKEN


TELEGRAM_APPLICATION = new_telegram_application(
    TELEGRAM_APPLICATION_TOKEN, get_session_factory, GRAPHS["email"]
)


def get_telegram_application() -> Application:
    return TELEGRAM_APPLICATION


######## Neo4j ########

NEO4J_CLIENT = Neo4jClient(
    driver=GraphDatabase.driver(
        uri=os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )
)


def get_neo4j_client() -> Neo4jClient:
    return NEO4J_CLIENT
