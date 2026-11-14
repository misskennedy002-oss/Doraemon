from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.ollama_client import stream_chat
from app.prompts.system import SYSTEM_PROMPT
import uuid

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str = ""

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(memory_block="")},
        {"role": "user", "content": request.message}
    ]

    async def generate():
        async for token in stream_chat(messages):
            # SSE format: each line must start with "data: "
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")