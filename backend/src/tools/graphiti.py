from datetime import datetime, timezone
from typing import Type

from graphiti_core.nodes import EpisodeType
from langchain_core.runnables.config import RunnableConfig
from pydantic import BaseModel

from tools.base import AsyncBaseTool


class AddEpisodeInput(BaseModel):
    name: str
    episode_body: str
    source: EpisodeType


class GraphitiAddEpisode(AsyncBaseTool):
    name: str = "graphiti_add_episode"
    description: str = """
        Add episode to Graphiti a long term graph based memory,
        use this to store memories about the user.
        An episode can be a user message, an incoming tool response, 
        that seems useful to keep in memory etc.
        Use it to store important information about the user,
        that can be used in future conversations.
        Always pass in the messages sent by the user and try to figure out
        important results from tool calls to pass in.

        name: find a short name that best describes the episode
        episode_body: the text of the episode
        source: the source of the episode, e.g.: user, tool_name (e.g. google_search)
    """
    args_schema: Type[BaseModel] = AddEpisodeInput

    async def _arun(
        self, name: str, episode_body: str, source: EpisodeType, config: RunnableConfig
    ) -> None:
        await self.dependencies.graphiti.add_episode(
            group_id=self._get_user_id(config),
            name=name,
            episode_body=episode_body,
            source=source,
            source_description="",
            reference_time=datetime.now(timezone.utc),
        )
