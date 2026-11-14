import httpx
import json
from typing import AsyncGenerator, List, Dict
from config import config

async def stream_chat(messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
    # [Keep your existing stream_chat code exactly as it is]
    url = f"{config.OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": config.MODEL_NAME,
        "messages": messages,
        "stream": True,
        "options": {"num_ctx": config.NUM_CTX, "temperature": 0.7}
    }
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]

# --- NEW FUNCTION ---
async def extract_memory_from_text(text: str) -> List[Dict[str, str]]:
    """Asks the model to extract facts from a user message."""
    prompt = f"""Extract any personal facts about the user from this message.
Return ONLY valid JSON in this exact format: {{"facts": [{{"fact": "User's name is Astha", "category": "name"}}]}}
If there are no facts, return {{"facts": []}}.

Message: {text}"""
    
    url = f"{config.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": config.MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json", # Force JSON output
        "options": {"temperature": 0.0} # 0 for strict extraction
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = json.loads(data.get("response", "{}"))
            return result.get("facts", [])
    except Exception as e:
        print(f"Memory extraction failed: {e}")
        return []