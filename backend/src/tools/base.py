from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from google.oauth2.credentials import Credentials
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.base import BaseTool
from pydantic import PrivateAttr

from models import User

if TYPE_CHECKING:
    from tools.toolkit import ToolDependencies

logger = logging.getLogger(__name__)


class AsyncBaseTool(BaseTool):
    handle_tool_error: bool = True
    handle_validation_error: bool = True
    verbose: bool = True
    _dependencies: ToolDependencies = PrivateAttr()
    _bound_user_id: str | None = PrivateAttr(default=None)
    user_confirmaton: bool = False

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._bound_user_id = None

    def with_dependencies(self, dependencies: ToolDependencies) -> AsyncBaseTool:
        self._dependencies = dependencies
        return self

    @property
    def dependencies(self) -> ToolDependencies:
        return self._dependencies

    async def get_user(self, config: RunnableConfig) -> User:
        user_id = self._get_user_id(config)
        async with self.dependencies.session_factory() as session:
            user = await session.get(User, user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            session.expunge(user)
        return user

    def bind_user_id(self, user_id: str) -> None:
        self._bound_user_id = user_id

    def _get_user_id(self, config: RunnableConfig) -> str:
        if self._bound_user_id:
            return self._bound_user_id
        return config["configurable"]["user_id"]

    def _run(self, *args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(self.arun(*args, **kwargs))

    def _create_credentials(
        self, user: User, scope: str, integration_key: str
    ) -> Credentials:
        credentials = Credentials(
            token=user.integrations.get(integration_key, {}).get("access_token"),
            refresh_token=user.integrations.get(integration_key, {}).get(
                "refresh_token"
            ),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.dependencies.google_client_id,
            client_secret=self.dependencies.google_client_secret,
            scopes=[scope],
        )
        return credentials
