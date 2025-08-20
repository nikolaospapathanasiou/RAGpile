from dataclasses import dataclass
from typing import Type

import httpx
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, PageElement
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel

from tools.base import AsyncBaseTool


class BrowserInput(BaseModel):
    url: str


async def parse_url(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    return get_text_with_links(soup)


def get_text_with_links(element: PageElement | Tag) -> str:
    if isinstance(element, NavigableString):
        return str(element)
    if not isinstance(element, Tag):
        return ""
    if element.name == "script":
        return ""
    if element.name == "a":
        return f"{element.get_text(strip=True)} ({element['href']})"
    res = ""
    for child in element.children:
        part = get_text_with_links(child).strip()
        if part:
            res += f"{part}\n"
    return res.strip()


@dataclass
class BrowserOutput:
    content: str


class BrowserTool(AsyncBaseTool):
    name: str = "browse_website"
    description: str = (
        "Browse a website and get back the stripped html content. The links are going to be preserved."
    )
    args_schema: Type[BaseModel] = BrowserInput

    async def _arun(self, url: str, config: RunnableConfig) -> BrowserOutput:
        content = await parse_url(url)
        return BrowserOutput(content=content)
