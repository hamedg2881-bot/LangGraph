import json
import time
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api.schemas import ChatCompletionRequest, ModelList, ModelObject
from app.model_selector import ModelSelectionError, select_model
from app.model_manager import ModelQueueFull, ModelQueueTimeout

router = APIRouter(prefix="/v1")


@router.get("/models", response_model=ModelList)
async def list_models(request: Request):
    return ModelList(
        data=[
            ModelObject(
                id="Auto",
                created=int(time.time()),
                owned_by="langgraph-agent",
            )
        ]
    )


@router.post("/chat/completions")
async def chat_completions(payload: ChatCompletionRequest, request: Request):
    if not payload.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    try:
        selected_model_id = await select_model(
            request.app.state.registry,
            request.app.state.settings,
            payload.messages,
        )
    except ModelSelectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    conversation_id = (
        payload.conversation_id
        or payload.chat_id
        or payload.model_dump().get("metadata", {}).get("chat_id")
    )

    thread_id = (
        f"{payload.user or 'anonymous'}:{conversation_id}"
        if conversation_id
        else f"request:{uuid.uuid4()}"
    )

    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    messages = []

    for item in payload.messages:
        if item.role in ("user", "human"):
            messages.append(HumanMessage(content=item.content))
        elif item.role in ("assistant", "ai"):
            messages.append(AIMessage(content=item.content))
        elif item.role in ("system", "developer"):
            messages.append(SystemMessage(content=item.content))
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported message role: {item.role}",
            )

    config = {
        "configurable": {
            "thread_id": thread_id,
            "model_id": selected_model_id,
        }
    }
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    if payload.stream:

        async def generate():
            def sse(data):
                return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            try:
                async with request.app.state.model_manager.lease(
                    selected_model_id,
                    timeout_seconds=request.app.state.settings.model_queue_timeout,
                ):
                    yield sse({
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": payload.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"role": "assistant"},
                        "finish_reason": None,
                    }],
                })

                    async for chunk, metadata in request.app.state.graph.astream(
                        {"messages": messages},
                        config=config,
                        stream_mode="messages",
                    ):
                        if metadata.get("langgraph_node") != "assistant":
                            continue

                        content = chunk.content

                        if isinstance(content, str) and content:
                            yield sse({
                                "id": completion_id,
                                "object": "chat.completion.chunk",
                                "created": created,
                                "model": payload.model,
                                "choices": [{
                                    "index": 0,
                                    "delta": {"content": content},
                                    "finish_reason": None,
                                }],
                            })

                yield sse({
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": payload.model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }],
                })

                yield "data: [DONE]\n\n"

            except ModelQueueFull:
                yield sse({"error": {"message": "Model request queue is full", "type": "rate_limit_error"}})
                yield "data: [DONE]\\n\\n"
            except Exception:
                yield sse({
                    "error": {
                        "message": "Agent streaming failed",
                        "type": "server_error",
                    }
                })
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        async with request.app.state.model_manager.lease(
            selected_model_id,
            timeout_seconds=request.app.state.settings.model_queue_timeout,
        ):
            result = await request.app.state.graph.ainvoke(
                {"messages": messages},
                config=config,
            )

        answer = result["messages"][-1]
        usage = answer.usage_metadata or {}

        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": payload.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer.content,
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

    except ModelQueueFull as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ModelQueueTimeout as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Agent inference failed",
        ) from exc
