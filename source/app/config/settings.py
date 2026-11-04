from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="/opt/ai/langgraph-agent/config/agent.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "LangGraph Agent"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8100, gt=0, le=65535)
    app_env: str = "production"

    dynamo_base_url: str = "http://127.0.0.1:8013/v1"
    dynamo_api_key: SecretStr = SecretStr("not-needed")
    dynamo_timeout: int = Field(default=180, gt=0)
    admin_api_key: SecretStr | None = None

    default_model: str = "qwen-coder"

    postgres_host: str = "127.0.0.1"
    postgres_port: int = Field(default=5432, gt=0, le=65535)
    postgres_db: str = "langgraph"
    postgres_user: str = "langgraph"
    postgres_password: SecretStr | None = None

    langgraph_checkpoint_enabled: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
