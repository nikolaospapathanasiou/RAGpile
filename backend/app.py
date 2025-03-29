import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from starlette.responses import StreamingResponse
from typing import List, Optional
from openai import OpenAI
import logging
import json
import asyncio
import uuid

from dotenv import load_dotenv

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session

from models import Datasource, Chat, Message


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
# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

# Allow all origins for development (change in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


@app.get("/")
async def hello():
    return "Hello, World!"


class InferenceRequest(BaseModel):
    model: str
    content: str
    chat_id: Optional[str] = None


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/chat")
async def openai_streaming(request: InferenceRequest, db: Session = Depends(get_db)):

    if not request.chat_id:
        words = request.content.split()
        title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")

        chat = Chat(
            id=str(uuid.uuid4()),
            title=title,
            user_id="a1b2c3d4-e5f6-4321-8765-abcdef123456",
        )
        db.add(chat)
        db.flush()
    else:
        chat = db.query(Chat).filter(Chat.id == request.chat_id).first()

    user_message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        content=request.content,
        is_from_user=True,
    )

    db.add(user_message)
    db.commit()
    

    # EAN VGALO AFTA TA 2 VARIABLES POU DN USARONTAI POYTHENA PETAEI ERROR
    # GT DN MPOREI NA VREI TO user_message STO SESSION META POU PROSPATHEI A KANEI yield sto line: 130. POLI PERIERGO PASA MOU
    asdf = user_message.id
    asdasd = user_message.chat_id

    chat_history = (
        db.query(Message)
        .filter(Message.chat_id == chat.id)
        .order_by(Message.created_at)
        .all()
    )

    messages = [
        {"role": "user" if msg.is_from_user else "assistant", "content": msg.content}
        for msg in chat_history
    ]

    messages.append({"role": "user", "content": request.content})

    completion = client.chat.completions.create(
        model=request.model,
        messages=messages,
        stream=True,
    )

    def stream_response():
        yield f'data: {{"id": {user_message.id}, "chat_id": {user_message.chat_id}}}'
        message_id = str(uuid.uuid4())
        full_ai_response = []
        for chunk in completion:
            logging.debug(f"Received chunk: {chunk}")

            content = getattr(chunk.choices[0].delta, "content", None)

            if content:
                full_ai_response.append(content)

            response_data = {
                "id": chunk.id,
                "message_id": message_id,
                "content": content,
                "finish_reason": chunk.choices[0].finish_reason,
                "index": chunk.choices[0].index,
            }

            yield f"data: {json.dumps(response_data)}\n\n"

        complete_response = "".join(full_ai_response)

        ai_message = Message(
            id=str(message_id),
            chat_id=chat.id,
            content=complete_response,
            is_from_user=False,
        )
        db.add(ai_message)
        db.commit()

    return StreamingResponse(stream_response(), media_type="text/event-stream")
