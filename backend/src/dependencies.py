import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from auth.token import TokenManager, get_current_user_factory

url = URL.create(
    drivername="postgresql",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="db",
    port=5432,
    database=os.environ["POSTGRES_DB"],
)


engine = create_engine(url)
SessionFactory = sessionmaker(bind=engine)


def get_session() -> Session:
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


token_manager = TokenManager(os.getenv("JWT_SECRET"))


def get_token_manager() -> TokenManager:
    return token_manager


get_current_user = get_current_user_factory(token_manager, get_session)
