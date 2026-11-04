import asyncio
import socket
import uuid
from contextlib import asynccontextmanager

class ModelQueueTimeout(Exception):
    pass


class ModelLease:
    def __init__(self, manager, request_id: str, model_id: str):
        self.manager = manager
        self.request_id = request_id
        self.model_id = model_id


class ModelManager:
    def __init__(
        self,
        database,
        max_active_per_model: int = 1,
        lease_seconds: int = 90,
        poll_seconds: float = 0.5,
    ):
        self.database = database
        self.max_active_per_model = max(1, max_active_per_model)
        self.lease_seconds = max(30, lease_seconds)
        self.poll_seconds = max(0.1, poll_seconds)
        self.owner = f"{socket.gethostname()}:{uuid.uuid4()}"

    async def enqueue(self, model_id: str, priority: int = 0) -> str:
        request_id = str(uuid.uuid4())
        async with self.database.pool.connection() as connection:
            await connection.execute(
                """
                INSERT INTO model_runtime_requests (id, model_id, owner, priority)
                VALUES (%s, %s, %s, %s)
                """,
                (request_id, model_id, self.owner, priority),
            )
        return request_id

    async def _try_claim(self, request_id: str, model_id: str) -> bool:
        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                await connection.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                    (model_id,),
                )
                await connection.execute(
                    """
                    DELETE FROM model_runtime_leases
                    WHERE expires_at < NOW()
                    """
                )
                await connection.execute(
                    """
                    UPDATE model_runtime_requests
                    SET state = 'failed', finished_at = NOW(),
                        error_code = 'lease_expired'
                    WHERE state = 'running' AND model_id = %s
                      AND id NOT IN (SELECT request_id FROM model_runtime_leases)
                    """,
                    (model_id,),
                )
                cursor = await connection.execute(
                    """
                    SELECT id
                    FROM model_runtime_requests
                    WHERE state = 'queued' AND model_id = %s
                    ORDER BY priority DESC, created_at, id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """,
                    (model_id,),
                )
                first = await cursor.fetchone()
                if first is None or str(first[0]) != request_id:
                    return False

                cursor = await connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM model_runtime_leases
                    WHERE model_id = %s AND expires_at >= NOW()
                    """,
                    (model_id,),
                )
                active = (await cursor.fetchone())[0]
                if active >= self.max_active_per_model:
                    return False

                cursor = await connection.execute(
                    """
                    UPDATE model_runtime_requests
                    SET state = 'running', started_at = NOW(), heartbeat_at = NOW()
                    WHERE id = %s AND state = 'queued'
                    RETURNING id
                    """,
                    (request_id,),
                )
                if await cursor.fetchone() is None:
                    return False

                await connection.execute(
                    """
                    INSERT INTO model_runtime_leases
                        (request_id, model_id, owner, expires_at)
                    VALUES (%s, %s, %s, NOW() + (%s * INTERVAL '1 second'))
                    """,
                    (request_id, model_id, self.owner, self.lease_seconds),
                )
                return True

    async def _heartbeat(self, request_id: str):
        while True:
            await asyncio.sleep(self.lease_seconds / 3)
            async with self.database.pool.connection() as connection:
                cursor = await connection.execute(
                    """
                    UPDATE model_runtime_leases
                    SET expires_at = NOW() + (%s * INTERVAL '1 second')
                    WHERE request_id = %s AND owner = %s
                    RETURNING request_id
                    """,
                    (self.lease_seconds, request_id, self.owner),
                )
                if await cursor.fetchone() is None:
                    return
                await connection.execute(
                    """
                    UPDATE model_runtime_requests
                    SET heartbeat_at = NOW()
                    WHERE id = %s AND state = 'running'
                    """,
                    (request_id,),
                )

    async def _finish(self, request_id: str, state: str, error_code: str | None = None):
        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                await connection.execute(
                    "DELETE FROM model_runtime_leases WHERE request_id = %s AND owner = %s",
                    (request_id, self.owner),
                )
                await connection.execute(
                    """
                    UPDATE model_runtime_requests
                    SET state = %s, finished_at = NOW(), error_code = %s
                    WHERE id = %s AND owner = %s AND state = 'running'
                    """,
                    (state, error_code, request_id, self.owner),
                )


    async def cancel_request(self, request_id: str):
        async with self.database.pool.connection() as connection:
            cursor = await connection.execute(
                """
                UPDATE model_runtime_requests
                SET state = 'cancelled', finished_at = NOW()
                WHERE id = %s AND state = 'queued'
                RETURNING id
                """,
                (request_id,),
            )
            return await cursor.fetchone() is not None

    async def cancel_queued(self, request_id: str):
        async with self.database.pool.connection() as connection:
            cursor = await connection.execute(
                """
                UPDATE model_runtime_requests
                SET state = 'cancelled', finished_at = NOW()
                WHERE id = %s AND owner = %s AND state = 'queued'
                RETURNING id
                """,
                (request_id, self.owner),
            )
            return await cursor.fetchone() is not None

    @asynccontextmanager
    async def lease(self, model_id: str, timeout_seconds: int = 600, priority: int = 0):
        request_id = await self.enqueue(model_id, priority)
        claimed = False
        try:
            loop = asyncio.get_running_loop()
            deadline = loop.time() + timeout_seconds
            while loop.time() < deadline:
                if await self._try_claim(request_id, model_id):
                    claimed = True
                    break
                await asyncio.sleep(self.poll_seconds)
            if not claimed:
                await self.cancel_queued(request_id)
                raise ModelQueueTimeout("Timed out waiting for a model execution slot")

            heartbeat = asyncio.create_task(self._heartbeat(request_id))
            try:
                yield ModelLease(self, request_id, model_id)
            except asyncio.CancelledError:
                await self._finish(request_id, "cancelled", "request_cancelled")
                raise
            except Exception:
                await self._finish(request_id, "failed", "inference_failed")
                raise
            else:
                await self._finish(request_id, "completed")
            finally:
                heartbeat.cancel()
                try:
                    await heartbeat
                except asyncio.CancelledError:
                    pass
        except BaseException:
            if not claimed:
                await self.cancel_queued(request_id)
            raise

    async def snapshot(self):
        async with self.database.pool.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT state, COUNT(*)
                FROM model_runtime_requests
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY state
                """
            )
            counts = {state: count for state, count in await cursor.fetchall()}
            cursor = await connection.execute(
                """
                SELECT model_id, COUNT(*)
                FROM model_runtime_leases
                WHERE expires_at >= NOW()
                GROUP BY model_id
                """
            )
            active = {model_id: count for model_id, count in await cursor.fetchall()}
            cursor = await connection.execute(
                """
                SELECT id, model_id, priority, created_at
                FROM model_runtime_requests
                WHERE state = 'queued'
                ORDER BY priority DESC, created_at, id
                LIMIT 100
                """
            )
            queued = [
                {"id": str(row[0]), "model_id": row[1], "priority": row[2],
                 "created_at": row[3].isoformat()}
                for row in await cursor.fetchall()
            ]
            return {"counts_24h": counts, "active_leases": active, "queued": queued}
