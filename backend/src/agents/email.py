from typing import Annotated

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


# llm = init_chat_model("google_genai:gemini-2.0-flash")


def chatbot(state: State) -> State:
    return {"messages": [llm.invoke(state["messages"])]}


def create_graph(checkpointer: PostgresSaver) -> CompiledGraph:
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    return graph_builder.compile(checkpointer)
