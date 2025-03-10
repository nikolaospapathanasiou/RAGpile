import json
import logging
import os
import time
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from .auth.router import auth_router

app = FastAPI()
app.include_router(auth_router)
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
    completion = client.chat.completions.create(
        model=request.model,
        messages=[
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ],
        stream=True,
    )

    def generator():
        for chunk in completion:
            logging.debug("Received chunk: %s", chunk)

            response_data = {
                "content": getattr(chunk.choices[0].delta, "content", None),
                "finish_reason": chunk.choices[0].finish_reason,
            }
            time.sleep(0.5)
            yield f"data: {json.dumps(response_data)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")
