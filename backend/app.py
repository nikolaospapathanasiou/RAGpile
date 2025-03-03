import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from starlette.responses import StreamingResponse
from typing import List
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

from models import Datasource,Chat,Message


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
    allow_origins=["*"],  # Change this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def hello():
    return "Hello, World!"


class MessageReq(BaseModel):
    role: str
    content: str


class InferenceRequest(BaseModel):
    model: str
    messages: List[MessageReq]
    chat_id: str
    user_id: str
    stream: bool


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.post("/chat")
async def openai_streaming(request: InferenceRequest, db: Session = Depends(get_db)):
    try:
        # Extract chat_id and user_id from the request
        chat_id = request.chat_id
        user_id = request.user_id

        # Check if the chat exists in the database
        existing_chat = db.query(Chat).filter(Chat.id == chat_id).first()
        
        # If chat doesn't exist, create a new one
        if not existing_chat:
            # Extract the first few words from the first user message to create a title
            default_title = "New Chat"
            title = default_title
            
            for msg in request.messages:
                if msg.role == "user" and msg.content:
                    # Create a title from the first user message
                    words = msg.content.split()
                    title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
                    break
            
            # Create new chat in database with the provided chat_id
            new_chat = Chat(
                id=chat_id,  # Use the provided chat_id
                user_id=user_id,
                title=title
                # created_at will be set automatically by SQLAlchemy
            )
            db.add(new_chat)
            db.commit()
            db.refresh(new_chat)
        
        # Store the user's message in the database
        for msg in request.messages:
            if msg.role == "user" and msg.content:
                # Only store the last user message
                user_message = Message(
                    id=str(uuid.uuid4()),
                    chat_id=chat_id,
                    content=msg.content,
                    is_from_user=True
                    # created_at will be set automatically
                )
                db.add(user_message)
                db.commit()
                break  # Just store the most recent user message

        # Create the streaming completion
        completion = client.chat.completions.create(
            model=request.model,
            messages=[
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            stream=True,
        )

        # Variable to accumulate the full AI response
        full_ai_response = []

        async def async_generator():
            for chunk in completion:
                logging.debug(f"Received chunk: {chunk}")

                # Extract content from the chunk
                content = getattr(chunk.choices[0].delta, "content", None)
                
                # Accumulate the full response
                if content:
                    full_ai_response.append(content)

                response_data = {
                    "id": chunk.id,
                    "object": chunk.object,
                    "created": chunk.created,
                    "model": chunk.model,
                    "chat_id": chat_id,
                    "system_fingerprint": chunk.system_fingerprint,
                    "choices": [
                        {
                            "index": chunk.choices[0].index,
                            "delta": {
                                "content": content
                            },
                            "finish_reason": chunk.choices[0].finish_reason,
                        }
                    ],
                }

                await asyncio.sleep(0)
                yield f"data: {json.dumps(response_data)}\n\n"
            
            # After streaming completes, store the AI's complete response
            try:
                # Join all the content chunks to form the complete response
                complete_response = "".join(full_ai_response)
                
                # Save the AI's response to the database
                ai_message = Message(
                    id=str(uuid.uuid4()),
                    chat_id=chat_id,
                    content=complete_response,
                    is_from_user=False
                    # created_at will be set automatically
                )
                db.add(ai_message)
                db.commit()
            except Exception as e:
                logging.error(f"Error saving AI response: {str(e)}")
                
            # End the stream
            yield "data: [DONE]\n\n"

        return StreamingResponse(async_generator(), media_type="text/event-stream")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
