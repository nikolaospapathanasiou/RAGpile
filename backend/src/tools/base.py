from typing import AsyncContextManager, Callable

from google.oauth2.credentials import Credentials
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.base import BaseTool
from pydantic.fields import PrivateAttr
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


class AsyncBaseTool(BaseTool):
    handle_tool_error: bool = True
    handle_validation_error: bool = True
    verbose: bool = True

    def _get_user_id(self, config: RunnableConfig) -> str:
        return config["configurable"]["user_id"]

    def _run(self, *args, **kwargs):
        raise ValueError("This should not happen")


class UserAwareBaseTool(AsyncBaseTool):
    _session_factory: Callable[[], AsyncContextManager[AsyncSession]] = PrivateAttr()

    async def _get_user(self, config: RunnableConfig) -> User:
        user_id = self._get_user_id(config)
        async with self._session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            session.expunge(user)
        return user


class GoogleBaseTool(UserAwareBaseTool):
    _client_id: str = PrivateAttr()
    _client_secret: str = PrivateAttr()

    def _create_credentials(
        self, user: User, scope: str, integration_key: str
    ) -> Credentials:
        credentials = Credentials(
            token=user.integrations.get(integration_key, {}).get("access_token"),
            refresh_token=user.integrations.get(integration_key, {}).get(
                "refresh_token"
            ),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=[scope],
        )
        return credentials
