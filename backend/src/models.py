from datetime import datetime, timezone

from sqlalchemy import PrimaryKeyConstraint, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import Executable, select, update


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    integrations: Mapped[dict[str, dict[str, str]]] = mapped_column(
        postgresql.JSONB, default={}, nullable=True
    )

    def has_active_integration(self, name: str):
        if name not in self.integrations:
            return False
        integration = self.integrations[name]
        if name == "email":
            utc_now = datetime.now(timezone.utc)
            utc_timestamp = int(utc_now.timestamp())
            refresh_token_expiry = integration.get("refresh_token_expiry")
            return (
                refresh_token_expiry is not None
                and int(refresh_token_expiry) > utc_timestamp
            )
        if name == "telegram":
            return "user_id" in integration
        raise ValueError(f"Unknown integration name {name}")

    @classmethod
    def select_user_from_telegram_id(cls, telegram_id: int) -> Executable:
        return select(cls).where(
            cls.integrations["telegram"]["user_id"].astext == str(telegram_id)
        )

    @classmethod
    def update_integrations(cls, user: "User") -> Executable:
        return (
            update(cls).where(cls.id == user.id).values(integrations=user.integrations)
        )


class Thread(Base):
    __tablename__ = "threads"

    thread_id: Mapped[str] = mapped_column(String)
    user_id: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(postgresql.TIMESTAMP, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("user_id", "thread_id"),)
