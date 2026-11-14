from fastapi import APIRouter, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Session as ChatSession, Message, Memory
from app.services.ollama_client import stream_chat, extract_memory_from_text
from app.prompts.system import SYSTEM_PROMPT
from config import config
import uuid
import re

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

async def process_memory_extraction(text: str):
    """Slow LLM background task for general facts."""
    facts = await extract_memory_from_text(text)
    if not facts:
        return
    
    db = SessionLocal()
    try:
        for f in facts:
            new_mem = Memory(fact=f["fact"], category=f.get("category", "general"))
            db.add(new_mem)
        db.commit()
    finally:
        db.close()

@router.post("/chat")
async def chat_endpoint(
    chat_req: ChatRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # 1. Handle Cookies
    session_id = request.cookies.get("session_id")
    is_new_session = False
    if not session_id:
        session_id = str(uuid.uuid4())
        is_new_session = True

    # --- DEBUG PRINTS ---
    print(f"\n--- NEW REQUEST ---")
    print(f"Session ID: {session_id}")

    # 2. Ensure Session exists
    session_record = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session_record:
        session_record = ChatSession(
            id=session_id, 
            prompt_version=config.PROMPT_VERSION, 
            model_name=config.MODEL_NAME
        )
        db.add(session_record)
        db.commit()

    # 3. Save User Message
    user_msg = Message(session_id=session_id, role="user", content=chat_req.message)
    db.add(user_msg)
    db.commit()

    # 4. Fetch Last 12 Messages
    last_12 = db.query(Message).filter(Message.session_id == session_id).order_by(Message.id.desc()).limit(12).all()
    last_12.reverse()
    print(f"Messages in context: {len(last_12)}")

    # 5. QUICK FIX: Save names instantly without waiting for the LLM
    name_match = re.search(r"(?:my name is|i am|call me)\s+([a-zA-Z]+)", chat_req.message, re.IGNORECASE)
    if name_match:
        extracted_name = name_match.group(1).capitalize()
        # Check if we already saved this name
        existing = db.query(Memory).filter(Memory.fact.contains(extracted_name)).first()
        if not existing:
            new_mem = Memory(fact=f"User's name is {extracted_name}", category="name")
            db.add(new_mem)
            db.commit()
            print(f"INSTANT MEMORY SAVED: User's name is {extracted_name}")

    # 6. Fetch Memories
    memories = db.query(Memory).all()
    memory_text = "Things you remember:\n"
    if memories:
        for m in memories:
            memory_text += f"- {m.fact}\n"
    else:
        memory_text = "No memories yet."
    
    print(f"Memory Block:\n{memory_text}")

    # 7. Build Prompt
    system_prompt = SYSTEM_PROMPT.format(memory_block=memory_text)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in last_12:
        messages.append({"role": msg.role, "content": msg.content})

    # 8. Trigger Slow Background Task for other facts
    background_tasks.add_task(process_memory_extraction, chat_req.message)

    # 9. Stream Response
    async def generate():
        full_response = ""
        async for token in stream_chat(messages):
            full_response += token
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"
        
        db_local = SessionLocal()
        try:
            bot_msg = Message(session_id=session_id, role="assistant", content=full_response)
            db_local.add(bot_msg)
            db_local.commit()
        finally:
            db_local.close()

    stream_response = StreamingResponse(generate(), media_type="text/event-stream")
    if is_new_session:
        stream_response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=31536000)
    
    return stream_response