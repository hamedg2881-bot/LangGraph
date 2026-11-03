from pathlib import Path

from psycopg_pool import AsyncConnectionPool


class RegistryDatabase:
    def __init__(self, conninfo: str):
        self.pool = AsyncConnectionPool(
            conninfo=conninfo,
            min_size=1,
            max_size=5,
            open=False,
        )

    async def open(self):
        await self.pool.open()
        await self.pool.wait()
        await self.initialize()

    async def initialize(self):
        schema_path = Path(__file__).with_name("schema.sql")
        schema = schema_path.read_text(encoding="utf-8")
        statements = [statement.strip() for statement in schema.split(";") if statement.strip()]

        async with self.pool.connection() as connection:
            async with connection.transaction():
                for statement in statements:
                    await connection.execute(statement)

    async def close(self):
        await self.pool.close()
