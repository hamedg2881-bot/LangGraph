from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    role: str
    content: str | list[str | dict]


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[ChatMessage]
    user: str | None = None
    conversation_id: str | None = None
    chat_id: str | None = None
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


class ModelObject(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "langgraph-agent"


class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelObject]
