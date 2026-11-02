from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph

from app.providers.dynamo import create_chat_model


SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Answer accurately and clearly. "
    "Use the conversation history when relevant."
)


def build_chat_graph(checkpointer, model=None):
    async def call_model(state: MessagesState, config: RunnableConfig):
        model_id = config.get("configurable", {}).get("model_id")
        if not model_id:
            raise RuntimeError("A selected model_id is required")
        chat_model = create_chat_model(model_id)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
        ]

        response = await chat_model.ainvoke(messages)

        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("assistant", call_model)
    builder.add_edge(START, "assistant")
    builder.add_edge("assistant", END)

    return builder.compile(checkpointer=checkpointer)
