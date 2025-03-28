import json
import logging
import os
import time
from typing import Annotated, List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from auth.router import auth_router
from dependencies import get_current_user
from models import User

app = FastAPI()
app.include_router(auth_router, prefix="/api")


@app.get("/api")
async def hello(current_user: Annotated[User, Depends(get_current_user)]):
    print(current_user)
    return "Hello, Woraaa"


class Message(BaseModel):
    role: str
    content: str


class InferenceRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/api/chat")
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
