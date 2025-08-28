from dataclasses import dataclass
from typing import AsyncContextManager, Callable, List, cast

from apscheduler.schedulers.base import BaseScheduler
from asyncpraw import Reddit
from graphiti_core import Graphiti
from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from tools.browser import BrowserTool
from tools.calendar import CalendarCreateEventTool, CalendarListEventsTool
from tools.email import GmailReadUnreadTool
from tools.graphiti import GraphitiAddEpisode
from tools.reddit import RedditSearchTool
from tools.scheduler import SchedulerCreateTool
from tools.search import GoogleSearchTool


@dataclass
class ToolDependencies:
    session_factory: Callable[[], AsyncContextManager[AsyncSession]]
    google_client_id: str
    google_client_secret: str
    google_search_api_key: str
    google_search_engine_id: str
    scheduler: BaseScheduler
    graphiti: Graphiti
    reddit_client: Reddit


class Toolkit:
    def __init__(self, dependencies: ToolDependencies):
        super().__init__()
        self.dependencies = dependencies

    def get_tools(self) -> List[BaseTool]:
        return cast(
            list[BaseTool],
            [
                # Calendar tools
                CalendarListEventsTool().with_dependencies(self.dependencies),
                CalendarCreateEventTool().with_dependencies(self.dependencies),
                # Email tools
                GmailReadUnreadTool().with_dependencies(self.dependencies),
                # Search tools
                GoogleSearchTool().with_dependencies(self.dependencies),
                # Scheduler tools
                SchedulerCreateTool().with_dependencies(self.dependencies),
                # Graphiti tools
                GraphitiAddEpisode().with_dependencies(self.dependencies),
                # Browser tools
                BrowserTool().with_dependencies(self.dependencies),
                # Reddit tools
                RedditSearchTool().with_dependencies(self.dependencies),
            ],
        )
