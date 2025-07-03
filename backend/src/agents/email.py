from typing import Annotated, Callable

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list, add_messages]


def completion(llm: BaseChatModel) -> Callable[[State], State]:
    def _completion(state: State) -> State:
        state["messages"].append(llm.invoke(state["messages"]))
        return state

    return _completion


def create_graph(checkpointer: PostgresSaver, llm: BaseChatModel) -> CompiledGraph:
    graph_builder = StateGraph(State)
    graph_builder.add_node("completion", completion(llm))
    graph_builder.add_edge(START, "completion")
    return graph_builder.compile(checkpointer)
