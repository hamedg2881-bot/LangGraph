from langchain_openai import ChatOpenAI

from app.config import get_settings


def create_chat_model(
    model: str | None = None,
    enable_thinking: bool | None = None,
) -> ChatOpenAI:
    settings = get_settings()
    thinking = settings.enable_thinking if enable_thinking is None else enable_thinking

    return ChatOpenAI(
        model=model or settings.default_model,
        base_url=settings.dynamo_base_url,
        api_key=settings.dynamo_api_key.get_secret_value(),
        temperature=0,
        timeout=settings.dynamo_timeout,
        max_retries=2,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": thinking,
            }
        },
    )
