import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Type

from googleapiclient.discovery import build  # type: ignore
from pydantic import BaseModel

from tools.base import AsyncBaseTool

logger = logging.getLogger(__name__)


class TimeFilter(str, Enum):
    DAY = "d"
    WEEK = "w"
    MONTH = "m"
    YEAR = "y"


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    display_link: str


class SearchInput(BaseModel):
    query: str
    time_filter: Optional[TimeFilter] = None


class GoogleSearchTool(AsyncBaseTool):
    name: str = "google_search"
    description: str = (
        "Search Google for information using the Google Custom Search API. "
        "Optional time_filter parameter accepts values: 'd' (past day), 'w' (past week), "
        "'m' (past month), 'y' (past year)"
    )
    args_schema: Type[BaseModel] = SearchInput

    async def _arun(
        self, query: str, time_filter: Optional[TimeFilter] = None, **_kwargs
    ) -> List[SearchResult]:
        service = build(
            "customsearch", "v1", developerKey=self.dependencies.google_search_api_key
        )

        search_params = {
            "q": query,
            "cx": self.dependencies.google_search_engine_id,
            "num": 10,
        }

        if time_filter:
            search_params["dateRestrict"] = time_filter.value

        result = service.cse().list(**search_params).execute()

        search_results = []
        items = result.get("items", [])

        for item in items:
            search_result = SearchResult(
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
                display_link=item.get("displayLink", ""),
            )
            search_results.append(search_result)
        return search_results
