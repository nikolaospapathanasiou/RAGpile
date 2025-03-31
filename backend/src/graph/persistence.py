from typing import Any, Callable

from pydantic_graph.persistence import (
    AbstractAsyncContextManager,
    BaseNode,
    BaseStatePersistence,
    End,
    NodeSnapshot,
    RunEndT,
    Snapshot,
    StateT,
)
from sqlalchemy.orm import Session


class PostgresPersistence(BaseStatePersistence):

    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    async def snapshot_node(
        self, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        pass

    async def snapshot_node_if_new(
        self, snapshot_id: str, state: StateT, next_node: BaseNode[StateT, Any, RunEndT]
    ) -> None:
        """Snapshot the state of a graph if the snapshot ID doesn't already exist in persistence.

        This method will generally call [`snapshot_node`][pydantic_graph.persistence.BaseStatePersistence.snapshot_node]
        but should do so in an atomic way.

        Args:
            snapshot_id: The ID of the snapshot to check.
            state: The state of the graph.
            next_node: The next node to run.
        """
        raise NotImplementedError

    async def snapshot_end(self, state: StateT, end: End[RunEndT]) -> None:
        """Snapshot the state of a graph when the graph has ended.

        This method should add an [`EndSnapshot`][pydantic_graph.persistence.EndSnapshot] to persistence.

        Args:
            state: The state of the graph.
            end: data from the end of the run.
        """
        raise NotImplementedError

    def record_run(self, snapshot_id: str) -> AbstractAsyncContextManager[None]:
        """Record the run of the node, or error if the node is already running.

        Args:
            snapshot_id: The ID of the snapshot to record.

        Raises:
            GraphNodeRunningError: if the node status it not `'created'` or `'pending'`.
            LookupError: if the snapshot ID is not found in persistence.

        Returns:
            An async context manager that records the run of the node.

        In particular this should set:

        - [`NodeSnapshot.status`][pydantic_graph.persistence.NodeSnapshot.status] to `'running'` and
          [`NodeSnapshot.start_ts`][pydantic_graph.persistence.NodeSnapshot.start_ts] when the run starts.
        - [`NodeSnapshot.status`][pydantic_graph.persistence.NodeSnapshot.status] to `'success'` or `'error'` and
          [`NodeSnapshot.duration`][pydantic_graph.persistence.NodeSnapshot.duration] when the run finishes.
        """
        raise NotImplementedError

    async def load_next(self) -> NodeSnapshot[StateT, RunEndT] | None:
        """Retrieve a node snapshot with status `'created`' and set its status to `'pending'`.

        This is used by [`Graph.iter_from_persistence`][pydantic_graph.graph.Graph.iter_from_persistence]
        to get the next node to run.

        Returns: The snapshot, or `None` if no snapshot with status `'created`' exists.
        """
        raise NotImplementedError

    async def load_all(self) -> list[Snapshot[StateT, RunEndT]]:
        """Load the entire history of snapshots.

        `load_all` is not used by pydantic-graph itself, instead it's provided to make it convenient to
        get all [snapshots][pydantic_graph.persistence.Snapshot] from persistence.

        Returns: The list of snapshots.
        """
        raise NotImplementedError
