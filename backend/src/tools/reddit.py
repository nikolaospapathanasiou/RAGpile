from dataclasses import dataclass
from enum import Enum

from asyncpraw.reddit import Submission
from pydantic import BaseModel

from tools.base import AsyncBaseTool


class TimeFilter(str, Enum):
    ALL = "all"
    DAY = "day"
    HOUR = "hour"
    MONTH = "month"
    WEEK = "week"
    YEAR = "year"


class RedditSearchInput(BaseModel):
    query: str
    time_filter: TimeFilter = TimeFilter.ALL


@dataclass
class RedditSearchResult:
    id: str
    title: str
    selftext: str
    link: str
    subreddit: str


class RedditSearchTool(AsyncBaseTool):
    name: str = "reddit_search"
    description: str = (
        "Searches Reddit for posts in all subreddits. "
        "After a search, get the details of the most relevant threads to get the comments."
    )

    args_schema: type[BaseModel] = RedditSearchInput

    async def _arun(
        self, query: str, time_filter: TimeFilter = TimeFilter.ALL, **kwargs
    ) -> list[RedditSearchResult]:
        subreddit = await self.dependencies.reddit_client.subreddit("all", fetch=False)
        results: list[RedditSearchResult] = []
        async for submission in subreddit.search(
            query,
            time_filter=time_filter.value,
            syntax="lucene",
            sort="hot",
            limit=50,
        ):
            if len(submission.selftext) > 3000:
                continue
            result = RedditSearchResult(
                id=submission.id,
                title=submission.title,
                selftext=submission.selftext,
                link=submission.url,
                subreddit=submission.subreddit.display_name,
            )
            results.append(result)

        return results


class RedditDetailsInput(BaseModel):
    post_id: str


@dataclass
class RedditDetails:
    top_comments: list[str]


class RedditDetailsTool(AsyncBaseTool):
    name: str = "reddit_details"
    description: str = (
        "Get the details of a post. "
        "You need to provide an id that you are going to find from the reddit_search tool"
    )
    args_schema: type[BaseModel] = RedditDetailsInput

    async def _arun(self, post_id: str, **kwargs) -> RedditDetails:
        submission: Submission = await self.dependencies.reddit_client.submission(
            post_id, fetch=False
        )
        submission.comment_limit = 20
        comments = await submission.comments()
        await comments.replace_more(limit=1)
        return RedditDetails(top_comments=[comment.body for comment in comments])
