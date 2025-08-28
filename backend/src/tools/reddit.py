from dataclasses import dataclass

from pydantic import BaseModel

from tools.base import AsyncBaseTool


class RedditSearchInput(BaseModel):
    query: str


@dataclass
class RedditSearchResult:
    title: str
    selftext: str
    link: str
    subreddit: str
    top_comments: list[str]


class RedditSearchTool(AsyncBaseTool):
    name: str = "reddit_search"
    description: str = "Searches Reddit for posts in all subreddits"

    args_schema: type[BaseModel] = RedditSearchInput

    async def _arun(self, query: str, **kwargs) -> list[RedditSearchResult]:
        subreddit = await self.dependencies.reddit_client.subreddit("all", fetch=False)
        results: list[RedditSearchResult] = []
        async for submission in subreddit.search(query):
            result = RedditSearchResult(
                title=submission.title,
                selftext=submission.selftext,
                link=submission.url,
                subreddit=submission.subreddit.display_name,
                top_comments=[],
            )

            comments = await submission.comments()
            await comments.replace_more(limit=1)
            for comment in comments:
                result.top_comments.append(comment.body)

            results.append(result)
        return results
