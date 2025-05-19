from sqlalchemy import String, func, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.base import Executable


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=True)
    config: Mapped[dict[str, str]] = mapped_column(
        postgresql.JSONB, default={}, nullable=False
    )

    def update_config(self, path: list[str], value: str) -> Executable:
        return (
            update(self.__class__)
            .where(self.__class__.id == self.id)
            .values(
                details=func.jsonb_set(
                    self.__class__.config,
                    f"{','.join(path)}",
                    value,
                    create_missing=True,
                )
            )
        )
