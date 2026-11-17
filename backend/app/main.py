from backend.app.services.personality import SYSTEM_PROMPT
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import traceback
import hashlib
import secrets
import hmac

from .database import get_connection

app = FastAPI(title="Doraemon API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "gemma3:4b"


{
    "role": "system",
    "content": SYSTEM_PROMPT
}

ITERATIONS = 310000


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


def hash_password(password):
    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        ITERATIONS
    )

    return f"{salt}${hashed.hex()}"


def verify_password(password, stored_hash):
    try:
        salt, original_hash = stored_hash.split("$")

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            ITERATIONS
        ).hex()

        return hmac.compare_digest(new_hash, original_hash)

    except (ValueError, TypeError):
        return False


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_current_user(
    authorization: str | None = Header(default=None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in first")

    token = authorization[7:].strip()

    if not token:
        raise HTTPException(401, "Invalid session")

    token_hash = hash_token(token)

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT users.id, users.username
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token_hash,)
        ).fetchone()

    if not user:
        raise HTTPException(401, "Invalid or expired session")

    return dict(user)


@app.get("/")
def home():
    return {"message": "Doraemon API is running!"}


# ---------------- AUTHENTICATION ----------------

@app.post("/api/auth/register")
def register(request: RegisterRequest):

    username = request.username.strip().lower()
    password = request.password

    if len(username) < 3 or len(username) > 30:
        raise HTTPException(
            400,
            "Username must be between 3 and 30 characters"
        )

    if not username.replace("_", "").isalnum():
        raise HTTPException(
            400,
            "Username can contain letters, numbers and underscores only"
        )

    if len(password) < 8:
        raise HTTPException(
            400,
            "Password must contain at least 8 characters"
        )

    with get_connection() as conn:

        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing:
            raise HTTPException(409, "Username already exists")

        cursor = conn.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (username, hash_password(password))
        )

        user_id = cursor.lastrowid

        # Give the first account ownership of old conversations.
        user_count = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        if user_count == 1:
            conn.execute(
                """
                UPDATE conversations
                SET user_id = ?
                WHERE user_id IS NULL
                """,
                (user_id,)
            )

        token = secrets.token_urlsafe(32)

        conn.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (hash_token(token), user_id)
        )

    return {
        "message": "Account created successfully",
        "token": token,
        "username": username
    }


@app.post("/api/auth/login")
def login(request: LoginRequest):

    username = request.username.strip().lower()

    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user or not verify_password(
            request.password,
            user["password_hash"]
        ):
            raise HTTPException(401, "Incorrect username or password")

        token = secrets.token_urlsafe(32)

        conn.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (hash_token(token), user["id"])
        )

    return {
        "message": "Login successful",
        "token": token,
        "username": username
    }


@app.post("/api/auth/logout")
def logout(user=Depends(get_current_user),
           authorization: str = Header()):

    token = authorization[7:].strip()

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE token = ?",
            (hash_token(token),)
        )

    return {"message": "Logged out successfully"}


@app.get("/api/auth/me")
def get_profile(user=Depends(get_current_user)):
    return user


# ---------------- CHAT HISTORY ----------------

@app.get("/api/conversations")
def get_conversations(user=Depends(get_current_user)):

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, created_at
            FROM conversations
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user["id"],)
        ).fetchall()

    return [dict(row) for row in rows]


@app.get("/api/conversations/{conversation_id}")
def get_messages(
    conversation_id: int,
    user=Depends(get_current_user)
):

    with get_connection() as conn:

        conversation = conn.execute(
            """
            SELECT id FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user["id"])
        ).fetchone()

        if not conversation:
            raise HTTPException(404, "Conversation not found")

        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id
            """,
            (conversation_id,)
        ).fetchall()

    return [dict(row) for row in rows]

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user=Depends(get_current_user)
):
    with get_connection() as conn:

        conversation = conn.execute(
            """
            SELECT id FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user["id"])
        ).fetchone()

        if not conversation:
            raise HTTPException(404, "Conversation not found")

        conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user["id"])
        )

    return {"message": "Conversation deleted successfully"}



# ---------------- AI CHAT ----------------

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user=Depends(get_current_user)
):
    try:
        with get_connection() as conn:

            conversation_id = request.conversation_id

            if conversation_id is None:

                cursor = conn.execute(
                    """
                    INSERT INTO conversations (title, user_id)
                    VALUES (?, ?)
                    """,
                    (request.message[:45], user["id"])
                )

                conversation_id = cursor.lastrowid

            else:

                exists = conn.execute(
                    """
                    SELECT id FROM conversations
                    WHERE id = ? AND user_id = ?
                    """,
                    (conversation_id, user["id"])
                ).fetchone()

                if not exists:
                    raise HTTPException(
                        404,
                        "Conversation not found"
                    )

            history = conn.execute(
                """
                SELECT role, content
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id
                """,
                (conversation_id,)
            ).fetchall()

        chat_messages = [
        {
        "role": "system",
        "content": SYSTEM_PROMPT
        }
        ]

        chat_messages.extend([
    {
        "role": row["role"],
        "content": row["content"]
    }
     for row in history
   ])

        chat_messages.append({
            "role": "user",
            "content": request.message
        })

        async with httpx.AsyncClient(timeout=300) as client:

            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "messages": chat_messages,
                    "stream": False
                }
            )

            response.raise_for_status()

            reply = response.json()["message"]["content"]

        with get_connection() as conn:

            conn.execute(
                """
                INSERT INTO messages
                (conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (conversation_id, "user", request.message)
            )

            conn.execute(
                """
                INSERT INTO messages
                (conversation_id, role, content)
                VALUES (?, ?, ?)
                """,
                (conversation_id, "assistant", reply)
            )

        return {
            "reply": reply,
            "conversation_id": conversation_id
        }

    except HTTPException:
        raise

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(error))
