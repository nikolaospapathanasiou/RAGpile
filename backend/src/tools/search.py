import logging
from dataclasses import dataclass
from typing import List, Type

from googleapiclient.discovery import build  # type: ignore
from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import BaseModel

from tools.base import AsyncBaseTool

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    display_link: str


class GoogleSearchToolkit(BaseToolkit):
    google_search_api_key: str
    google_search_engine_id: str

    def get_tools(self) -> List[BaseTool]:
        return [
            GoogleSearchTool(
                google_search_api_key=self.google_search_api_key,
                google_search_engine_id=self.google_search_engine_id,
            )
        ]


class SearchInput(BaseModel):
    query: str


class GoogleSearchTool(AsyncBaseTool):
    name: str = "google_search"
    description: str = (
        "Search Google for information using the Google Custom Search API"
    )
    args_schema: Type[BaseModel] = SearchInput

    google_search_api_key: str
    google_search_engine_id: str

    async def _arun(self, query: str) -> List[SearchResult]:
        service = build("customsearch", "v1", developerKey=self.google_search_api_key)

        result = (
            service.cse()
            .list(q=query, cx=self.google_search_engine_id, num=10)
            .execute()
        )

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
