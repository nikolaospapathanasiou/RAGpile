from datetime import datetime, timedelta, timezone
from typing import AsyncContextManager, Callable
from uuid import uuid4
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from models import Thread, User


class Agent:
    def __init__(
        self,
        graph: CompiledStateGraph,
        session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    ) -> None:
        self.session_factory = session_factory
        self.graph = graph

    async def get_current_thread_id(self, user: User) -> str:
        async with self.session_factory() as session:
            thread_id = user.integrations["telegram"].get("thread_id")
            last_message_at = user.integrations["telegram"].get("last_message_at")
            if (
                not thread_id
                or not last_message_at
                or (
                    datetime.fromisoformat(last_message_at)
                    < datetime.now(tz=timezone.utc) - timedelta(hours=2)
                )
            ):
                thread_id = uuid4().hex
                session.add(
                    Thread(
                        id=thread_id,
                        user_id=user.id,
                        created_at=datetime.now(),
                    )
                )
                user.integrations["telegram"]["thread_id"] = thread_id
            user.integrations["telegram"]["last_message_at"] = datetime.now(
                tz=timezone.utc
            ).isoformat()

            await session.execute(User.update_integrations(user))
        return thread_id
