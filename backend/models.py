from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, ForeignKey, JSON, Text, DateTime
from typing import List
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    
    chats: Mapped[List["Chat"]] = relationship(back_populates="user")



class Datasource(Base):
    __tablename__ = "datasources"
    
    id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)

    def __repr__(self):
        return f"<Datasource(id={self.id}, owner_id={self.owner_id})>"
    
class Chat(Base):
    __tablename__ = "chats"
    
    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="chats")
    messages: Mapped[List["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, user_id={self.user_id}, title={self.title})>"

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(Uuid, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id: Mapped[str] = mapped_column(ForeignKey("chats.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_from_user: Mapped[bool] = mapped_column(nullable=False)  # True if from user, False if from AI
    
    # Relationship
    chat: Mapped["Chat"] = relationship(back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, is_from_user={self.is_from_user})>"