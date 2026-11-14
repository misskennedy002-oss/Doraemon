from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True) # UUID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    prompt_version = Column(String, default="v1")
    model_name = Column(String)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    role = Column(String) # "user" or "assistant" or "system"
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Index for fast querying of last 12 messages
    __table_args__ = (Index("ix_messages_session_id_id", "session_id", "id"),)

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fact = Column(String)
    category = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())