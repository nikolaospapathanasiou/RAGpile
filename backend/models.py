from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, ForeignKey, JSON
from typing import List


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(Uuid, primary_key=True)


class Datasource(Base):
    __tablename__ = "datasources"
    
    id: Mapped[str] = mapped_column(Uuid, primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    config: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)

    def __repr__(self):
        return f"<Datasource(id={self.id}, owner_id={self.owner_id})>"
    