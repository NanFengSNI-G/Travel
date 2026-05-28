import json
import uuid
import logging

from pydantic import BaseModel, Field
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.agents.workflow import graph

router = APIRouter()
log = logging.getLogger('graph')


# ── Schemas ──────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(description='用户输入的消息')
    thread_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description='会话ID')
    passenger_id: str = Field(default="3442 587242", description='旅客ID')


# ── Routes ───────────────────────────────────────────────────────────

@router.post('/graph/')
async def chat(req: ChatRequest):
    config = {
        "configurable": {
            "passenger_id": req.passenger_id,
            "thread_id": req.thread_id,
        }
    }

    async def generate():
        try:
            if req.message.strip().lower() != 'y':
                input_data = {"messages": ("user", req.message)}
            else:
                input_data = None

            async for chunk in graph.astream(input_data, config, stream_mode="custom"):
                tag, content = chunk
                if tag == "token":
                    yield f"data: {json.dumps({'content': content, 'type': 'token'}, ensure_ascii=False)}\n\n"

            current_state = graph.get_state(config)
            if current_state.next:
                prompt = (
                    "AI助手马上根据你要求，执行相关操作。"
                    "您是否批准上述操作？输入 'y' 继续；否则，请说明您请求的更改。\n"
                )
                yield f"data: {json.dumps({'content': prompt, 'type': 'approval'}, ensure_ascii=False)}\n\n"

            yield f"data: [DONE]\n\n"
        except Exception:
            log.exception("流式响应异常")
            yield f"data: {json.dumps({'error': '服务器内部错误', 'type': 'error'}, ensure_ascii=False)}\n\n"
            yield f"data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
