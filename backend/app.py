import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from starlette.responses import StreamingResponse
from typing import List
from openai import OpenAI
import logging
import json
import asyncio

from dotenv import load_dotenv

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from models import Datasource


load_dotenv()

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

# Allow all origins for development (change in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def hello():
    return "Hello, World!"


class Message(BaseModel):
    role: str
    content: str


class InferenceRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/chat")
async def openai_streaming(request: InferenceRequest):
    try:
        completion = client.chat.completions.create(
            model=request.model,
            messages=[
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            stream=True,
        )

        async def async_generator():
            for chunk in completion:
                logging.debug(f"Received chunk: {chunk}")

                response_data = {
                    "id": chunk.id,
                    "object": chunk.object,
                    "created": chunk.created,
                    "model": chunk.model,
                    "system_fingerprint": chunk.system_fingerprint,
                    "choices": [
                        {
                            "index": chunk.choices[0].index,
                            "delta": {
                                "content": getattr(
                                    chunk.choices[0].delta, "content", None
                                )
                            },
                            "finish_reason": chunk.choices[0].finish_reason,
                        }
                    ],
                }

                await asyncio.sleep(0)
                yield f"data: {json.dumps(response_data)}\n\n"

        return StreamingResponse(async_generator(), media_type="text/event-stream")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
