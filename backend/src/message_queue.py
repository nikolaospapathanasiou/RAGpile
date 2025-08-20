import threading
from asyncio import Queue
from dataclasses import dataclass
from typing import Generic, TypeVar

from langchain_core.messages import BaseMessage

T = TypeVar("T")


class FanoutQueue(Generic[T]):
    def __init__(self):
        self._queues: dict[str, Queue[T]] = {}
        self._lock = threading.Lock()

    def register(self, name: str):
        with self._lock:
            if name in self._queues:
                raise ValueError(f"Queue {name} already exists")
            self._queues[name] = Queue[T]()

    async def get(self, name: str) -> T:
        return await self._queues[name].get()

    async def put(self, item: T) -> None:
        for queue in self._queues.values():
            await queue.put(item)

    async def shutdown(self):
        for queue in self._queues.values():
            queue.shutdown()


@dataclass
class MessageWithUserId:
    user_id: str
    message: BaseMessage


class MessageQueue(FanoutQueue[MessageWithUserId]):
    pass
