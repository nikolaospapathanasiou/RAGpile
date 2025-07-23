from typing import Annotated, AsyncContextManager, Callable

from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypedDict

from tools.email import GmailToolkit


class State(TypedDict):
    messages: Annotated[list, add_messages]


def completion(
    llm: Runnable[LanguageModelInput, BaseMessage],
) -> Callable[[State], State]:
    def _completion(state: State) -> State:
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    return _completion


def should_continue(state: State) -> str:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END


def create_graph(
    checkpointer: AsyncPostgresSaver,
    llm: BaseChatModel,
    session_factory: Callable[[], AsyncContextManager[AsyncSession]],
    client_id: str,
    client_secret: str,
) -> CompiledStateGraph:
    tools = GmailToolkit(
        session_factory=session_factory,
        client_id=client_id,
        client_secret=client_secret,
    ).get_tools()
    llm_with_tools = llm.bind_tools(tools)

    tool_node = ToolNode(tools)

    graph_builder = StateGraph(State)
    graph_builder.add_node("completion", RunnableLambda(completion(llm_with_tools)))
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_edge(START, "completion")
    graph_builder.add_conditional_edges("completion", should_continue)
    graph_builder.add_edge("tools", "completion")

    return graph_builder.compile(checkpointer)
