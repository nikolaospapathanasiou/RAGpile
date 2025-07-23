from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row


class LazyAsyncPostgresSaver(AsyncPostgresSaver):
    def __init__(self, conn_string: str):
        self.conn_string = conn_string
        super().__init__(None)

    async def connect(self) -> None:
        self.conn = await AsyncConnection.connect(
            self.conn_string, autocommit=True, prepare_threshold=0, row_factory=dict_row
        )

    async def close(self) -> None:
        await self.conn.close()
