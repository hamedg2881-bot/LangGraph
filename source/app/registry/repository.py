from psycopg.types.json import Jsonb


class ModelRegistryRepository:
    def __init__(self, database):
        self.database = database


    async def register_manual_model(
        self,
        model_id: str,
        display_name: str,
        provider: str,
        architecture: str | None,
        quantization: str | None,
        context_length: int | None,
        capabilities: list[str],
        notes: str | None = None,
    ):
        allowed = {"chat", "vision", "reasoning", "coding", "tool_calling"}
        normalized = set(capabilities)
        if not normalized.issubset(allowed):
            raise ValueError("Unsupported model capability")

        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                cursor = await connection.execute(
                    """
                    INSERT INTO model_registry_models (
                        id, display_name, provider, architecture, quantization,
                        context_length, approval_status, is_enabled, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 'pending', FALSE,
                            %s)
                    ON CONFLICT (id) DO NOTHING
                    RETURNING id
                    """,
                    (
                        model_id, display_name, provider, architecture,
                        quantization, context_length,
                        Jsonb({"registration_source": "manual"}),
                    ),
                )
                if await cursor.fetchone() is None:
                    return False

                for capability in sorted(normalized):
                    await connection.execute(
                        """
                        INSERT INTO model_registry_capabilities (model_id, capability)
                        VALUES (%s, %s)
                        """,
                        (model_id, capability),
                    )

                await connection.execute(
                    """
                    INSERT INTO model_registry_approvals
                        (model_id, action, actor, notes)
                    VALUES (%s, 'updated', 'admin', %s)
                    """,
                    (model_id, notes or "Manual registration; pending approval"),
                )
        return True

    async def sync_discovered_models(self, models: list[dict]):
        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                for model in models:
                    model_id = model.get("id")
                    if not model_id:
                        continue

                    metadata = {
                        key: value
                        for key, value in model.items()
                        if key not in {"id", "object", "created", "owned_by", "context_window"}
                    }

                    await connection.execute(
                        """
                        INSERT INTO model_registry_models (
                            id,
                            display_name,
                            provider,
                            context_length,
                            last_seen_at,
                            metadata
                        )
                        VALUES (%s, %s, %s, %s, NOW(), %s)
                        ON CONFLICT (id) DO UPDATE SET
                            last_seen_at = NOW(),
                            updated_at = NOW()
                        """,
                        (
                            model_id,
                            model_id,
                            model.get("owned_by") or "nvidia-dynamo",
                            model.get("context_window"),
                            Jsonb(metadata),
                        ),
                    )

    async def list_models(self):
        async with self.database.pool.connection() as connection:
            cursor = await connection.execute(
                """
                SELECT
                    m.id,
                    m.display_name,
                    m.provider,
                    m.architecture,
                    m.quantization,
                    m.context_length,
                    m.approval_status,
                    m.is_enabled,
                    m.first_seen_at,
                    m.last_seen_at,
                    m.metadata,
                    COALESCE(
                        ARRAY_AGG(c.capability) FILTER (WHERE c.capability IS NOT NULL),
                        ARRAY[]::TEXT[]
                    ) AS capabilities
                FROM model_registry_models AS m
                LEFT JOIN model_registry_capabilities AS c ON c.model_id = m.id
                GROUP BY m.id
                ORDER BY m.display_name
                """
            )
            return await cursor.fetchall()

    async def record_decision(
        self,
        model_id: str,
        action: str,
        actor: str = "admin",
        notes: str | None = None,
    ):
        async with self.database.pool.connection() as connection:
            await connection.execute(
                """
                INSERT INTO model_registry_approvals (model_id, action, actor, notes)
                VALUES (%s, %s, %s, %s)
                """,
                (model_id, action, actor, notes),
            )

    async def set_approval(
        self,
        model_id: str,
        approved: bool,
        actor: str = "admin",
        notes: str | None = None,
    ):
        status = "approved" if approved else "rejected"
        action = status

        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                cursor = await connection.execute(
                    """
                    UPDATE model_registry_models
                    SET approval_status = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (status, model_id),
                )
                if await cursor.fetchone() is None:
                    return False

                await connection.execute(
                    """
                    INSERT INTO model_registry_approvals (model_id, action, actor, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (model_id, action, actor, notes),
                )
        return True

    async def set_enabled(
        self,
        model_id: str,
        enabled: bool,
        actor: str = "admin",
        notes: str | None = None,
    ):
        action = "enabled" if enabled else "disabled"

        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                cursor = await connection.execute(
                    """
                    UPDATE model_registry_models
                    SET is_enabled = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (enabled, model_id),
                )
                if await cursor.fetchone() is None:
                    return False

                await connection.execute(
                    """
                    INSERT INTO model_registry_approvals (model_id, action, actor, notes)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (model_id, action, actor, notes),
                )
        return True

    async def update_model(self, model_id: str, fields: dict):
        allowed_fields = {
            "display_name",
            "architecture",
            "quantization",
            "context_length",
        }
        updates = {
            key: value
            for key, value in fields.items()
            if key in allowed_fields
        }

        if not updates:
            return False

        assignments = ", ".join(f"{key} = %s" for key in updates)
        values = list(updates.values())

        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                cursor = await connection.execute(
                    f"""
                    UPDATE model_registry_models
                    SET {assignments}, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (*values, model_id),
                )
                if await cursor.fetchone() is None:
                    return False

                await connection.execute(
                    """
                    INSERT INTO model_registry_approvals (model_id, action, actor, notes)
                    VALUES (%s, 'updated', 'admin', NULL)
                    """,
                    (model_id,),
                )
        return True

    async def set_capabilities(self, model_id: str, capabilities: list[str]):
        allowed = {"chat", "vision", "reasoning", "coding", "tool_calling"}
        normalized = set(capabilities)

        if not normalized.issubset(allowed):
            raise ValueError("Unsupported model capability")

        async with self.database.pool.connection() as connection:
            async with connection.transaction():
                cursor = await connection.execute(
                    "SELECT id FROM model_registry_models WHERE id = %s",
                    (model_id,),
                )
                if await cursor.fetchone() is None:
                    return False

                await connection.execute(
                    "DELETE FROM model_registry_capabilities WHERE model_id = %s",
                    (model_id,),
                )

                for capability in sorted(normalized):
                    await connection.execute(
                        """
                        INSERT INTO model_registry_capabilities (model_id, capability)
                        VALUES (%s, %s)
                        """,
                        (model_id, capability),
                    )
        return True
