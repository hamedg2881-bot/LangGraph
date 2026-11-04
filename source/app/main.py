from contextlib import asynccontextmanager

from fastapi import FastAPI

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.conninfo import make_conninfo

from app.api.routes import router
from app.api.admin_routes import router as admin_router, model_manager_router
from app.config import get_settings
from app.graph import build_chat_graph
from app.registry.database import RegistryDatabase
from app.registry.repository import ModelRegistryRepository
from app.model_manager import ModelManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    if settings.postgres_password is None:
        raise RuntimeError("PostgreSQL password is not configured")

    conn_string = make_conninfo(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
    )

    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        registry_database = RegistryDatabase(conn_string)

        try:
            await registry_database.open()
            app.state.settings = settings
            app.state.checkpointer = checkpointer
            app.state.graph = build_chat_graph(checkpointer=checkpointer)
            app.state.registry_database = registry_database
            app.state.registry = ModelRegistryRepository(registry_database)
            app.state.model_manager = ModelManager(
                registry_database,
                max_active_per_model=settings.model_max_active_per_model,
            )
            yield
        finally:
            await registry_database.close()


app = FastAPI(
    title="LangGraph Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(admin_router)
app.include_router(model_manager_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
