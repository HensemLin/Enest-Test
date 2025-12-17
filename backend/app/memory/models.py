from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

from ..database import Base


class ChatSession(Base):
    """Model for chat sessions with multi-PDF support."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    pdf_ids = Column(ARRAY(Integer))  # Array of PDF IDs for multi-PDF conversations
    user_id = Column(String(255), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    summary = Column(Text)  # Rolling conversation summary
    total_messages = Column(Integer, default=0)
    session_metadata = Column(JSONB)  # Extracted entities, key topics, etc.


class ChatMessage(Base):
    """Model for individual chat messages."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, nullable=False)
    session_id = Column(String(255), ForeignKey('chat_sessions.session_id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    sources = Column(JSONB)  # [{pdf_id: 1, page: 5, chunk: "..."}]
    token_count = Column(Integer)
