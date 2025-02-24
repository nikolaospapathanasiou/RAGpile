import os

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

url = URL.create(
    drivername="postgresql",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="db",
    port=5432,
    database=os.environ["POSTGRES_DB"],
)


engine = create_engine(url)


app = FastAPI()


@app.get("/")
async def hello():
    return "Hello, World!"
