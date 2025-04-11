import os
from typing import AsyncIterator

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from auth.token import TokenManager, get_current_user_factory

url = URL.create(
    drivername="postgresql+asyncpg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="db",
    port=5432,
    database=os.environ["POSTGRES_DB"],
)


engine = create_async_engine(url, echo=True)
SessionFactory = async_sessionmaker(bind=engine)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        async with session.begin():
            yield session


token_manager = TokenManager(os.environ["JWT_SECRET"])


def get_token_manager() -> TokenManager:
    return token_manager


get_current_user = get_current_user_factory(token_manager, get_session)
