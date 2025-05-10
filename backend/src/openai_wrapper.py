import json
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import OpenAI
from openai.resources.models import Model, SyncPage
from pydantic import BaseModel

from dependencies import get_openai_client

openai_router = APIRouter()


@openai_router.get("/models", response_model=SyncPage[Model])
async def list_models(openai: OpenAI = Depends(get_openai_client)):
    return openai.models.list()


class Message(BaseModel):
    role: str
    content: str


class InferenceRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool


@openai_router.post("/chat")
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

            response_data = {
                "content": getattr(chunk.choices[0].delta, "content", None),
                "finish_reason": chunk.choices[0].finish_reason,
            }
            yield f"data: {json.dumps(response_data)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")
