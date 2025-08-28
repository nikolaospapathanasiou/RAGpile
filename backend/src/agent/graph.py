from datetime import datetime
from typing import Annotated, AsyncContextManager, Callable

from apscheduler.schedulers.base import BaseScheduler
from asyncpraw import Reddit
from graphiti_core import Graphiti
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.messages.system import SystemMessage
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.tools.base import BaseTool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypedDict

from agent.agent import Agent
from message_queue import MessageQueue
from tools.toolkit import ToolDependencies, Toolkit


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


DEFAULT_SYSTEM_PROMPT = """
You are a helpful peronal assistant.
The time is {now}.
The responses are delivered through Telegram, so keep them short.
The parse_mode of the message is html so you can use html tags.
Specifically only b,i,u,s,a,code,pre,blockquote are supported.
DO NOT use ul, li, br or span they are not supported.
Whenever you want to send code, surround it with <code class="language-python">...</code>.
In the background, there are scheduled jobs running that may send messages in the thread.
"""


def get_system_message() -> SystemMessage:
    return SystemMessage(DEFAULT_SYSTEM_PROMPT.format(now=datetime.now().isoformat()))


def completion(
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Callable[[State], State]:
    def _completion(state: State) -> State:
        last_message = state["messages"][-1]
        if last_message.type == "ai":
            return state
        system_prompt = get_system_message()
        response = llm.invoke([system_prompt] + state["messages"])
        return {"messages": [response]}

    return _completion


def should_continue(state: State) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


def create_tools(
    graphiti: Graphiti,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    client_id: str,
    client_secret: str,
    google_search_api_key: str,
    google_search_engine_id: str,
    scheduler: BaseScheduler,
    reddit_client: Reddit,
) -> list[BaseTool]:
    dependencies = ToolDependencies(
        session_factory=session_factory,
        google_client_id=client_id,
        google_client_secret=client_secret,
        google_search_api_key=google_search_api_key,
        google_search_engine_id=google_search_engine_id,
        scheduler=scheduler,
        graphiti=graphiti,
        reddit_client=reddit_client,
    )

    toolkit = Toolkit(dependencies)
    return toolkit.get_tools()


def create_agent(
    checkpointer: AsyncPostgresSaver,
    llm: BaseChatModel,
    tools: list[BaseTool],
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    queue: MessageQueue,
) -> Agent:

    llm_with_tools = llm.bind_tools(tools)

    tool_node = ToolNode(tools)

    graph_builder = StateGraph(State)
    graph_builder.add_node("completion", RunnableLambda(completion(llm_with_tools)))
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "completion")
    graph_builder.add_conditional_edges("completion", should_continue)
    graph_builder.add_edge("tools", "completion")
    graph = graph_builder.compile(checkpointer)
    return Agent(graph, session_factory, queue)
