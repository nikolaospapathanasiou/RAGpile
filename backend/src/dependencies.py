import os

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

url = URL.create(
    drivername="postgresql",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="db",
    port=5432,
    database=os.environ["POSTGRES_DB"],
)


engine = create_engine(url)
Session = sessionmaker(bind=engine)


def get_session() -> Session:
    db = Session()
    try:
        yield db
    finally:
        db.close()
