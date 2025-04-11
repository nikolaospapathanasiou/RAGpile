import json
import logging
import os
import time
from typing import Annotated, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth.router import auth_router
from dependencies import get_current_user, get_session
from models import User

app = FastAPI()
app.include_router(auth_router, prefix="/ragpile/api")

logger = logging.getLogger(__name__)


@app.get("/ragpile/api")
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


class Webhook(BaseModel):
    action: str
    message: str
    user: Optional[str]


class WebhookUser(BaseModel):
    id: str
    name: str
    email: str
    profile_image_url: str


@app.post("/webhook")
async def webhook(db: Annotated[AsyncSession, Depends(get_session)], request: Webhook):
    # {
    #   "action": "signup",
    #   "message": "New user signed up: Stavros",
    #   "user": "{
    #       \"id\":\"be36236b-18b4-41f9-b717-2a64fdd654b9\",
    #       \"name\":\"Stavros\",
    #       \"email\":\"stavros.champilomatis@gmail.com\",
    #       \"role\":\"pending\",
    #       \"profile_image_url\":\"...",
    #       \"last_active_at\":1744376774,
    #       \"updated_at\":1744376774,
    #       \"created_at\":1744376774,
    #       \"oauth_sub\":\"google@100223762578536717199\"
    #   }"
    if request.action != "signup":
        return {"status": "ok"}
    if not request.user:
        logger.error("No user in webhook")
        raise HTTPException(status_code=400, detail="No user in webhook")

    webhook_user = WebhookUser.parse_raw(request.user)
    user = User(id=webhook_user.id, name=webhook_user.name, email=webhook_user.email)
    db.add(user)
    await db.commit()
    return {"status": "ok"}


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
