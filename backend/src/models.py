from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
        raise ValueError(f"Unknown integration name {name}")
