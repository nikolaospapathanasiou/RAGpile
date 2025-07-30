from typing import AsyncContextManager, Callable

from google.oauth2.credentials import Credentials
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.base import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


class AsyncBaseTool(BaseTool):
    handle_tool_error: bool = True
    handle_validation_error: bool = True
    verbose: bool = True

    def _run(self, *args, **kwargs):
        raise ValueError("This should not happen")


class UserAwareBaseTool(AsyncBaseTool):
    session_factory: Callable[[], AsyncContextManager[AsyncSession]]

    async def _get_user(self, config: RunnableConfig) -> User:
        user_id = config["configurable"]["user_id"]
        async with self.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            session.expunge(user)
        return user


class GoogleBaseTool(UserAwareBaseTool):
    client_id: str
    client_secret: str

    def _create_credentials(
        self, user: User, scope: str, integration_key: str
    ) -> Credentials:
        credentials = Credentials(
            token=user.integrations.get(integration_key, {}).get("access_token"),
            refresh_token=user.integrations.get(integration_key, {}).get(
                "refresh_token"
            ),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[scope],
        )
        return credentials
