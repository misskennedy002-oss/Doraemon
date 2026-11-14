import httpx
import json
from typing import AsyncGenerator, List, Dict
from config import config

async def stream_chat(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    url = f"{config.OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": config.MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {
            "num_ctx": config.NUM_CTX,
            "temperature": 0.7,
        }
    }
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]