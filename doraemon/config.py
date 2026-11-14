import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:4b")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    NUM_CTX = int(os.getenv("NUM_CTX", 4096))
    PROMPT_VERSION = "v1"

config = Config()