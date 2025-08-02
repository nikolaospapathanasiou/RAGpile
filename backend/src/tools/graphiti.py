from datetime import datetime, timezone
from typing import ClassVar, Type

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools.base import BaseToolkit
from pydantic import BaseModel
from pydantic.fields import PrivateAttr

from tools.base import AsyncBaseTool


class GraphitiToolkit(BaseToolkit):
    _graphiti: Graphiti = PrivateAttr()

    def __init__(self, graphiti: Graphiti):
        super().__init__()
        self._graphiti = graphiti

    def get_tools(self):
        add_episode_tool = GraphitiAddEpisode()
        add_episode_tool._graphiti = self._graphiti
        return [add_episode_tool]


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
    _graphiti: Graphiti = PrivateAttr()

    async def _arun(
        self, name: str, episode_body: str, source: EpisodeType, config: RunnableConfig
    ) -> None:
        await self._graphiti.add_episode(
            group_id=self._get_user_id(config),
            name=name,
            episode_body=episode_body,
            source=source,
            source_description="",
            reference_time=datetime.now(timezone.utc),
        )
