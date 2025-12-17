from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    """Schema for creating a new chat message."""

    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    sources: Optional[List[dict]] = None
    token_count: Optional[int] = None


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

    id: int
    session_id: str
    role: str
    content: str
    timestamp: datetime
    sources: Optional[List[dict]] = None
    token_count: Optional[int] = None

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session."""

    session_id: str
    pdf_ids: List[int]
    user_id: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""

    id: int
    session_id: str
    pdf_ids: List[int]
    user_id: Optional[str] = None
    created_at: datetime
    last_activity: datetime
    summary: Optional[str] = None
    total_messages: int
    session_metadata: Optional[dict] = None

    class Config:
        from_attributes = True


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session."""

    summary: Optional[str] = None
    total_messages: Optional[int] = None
    session_metadata: Optional[dict] = None


class MemoryContext(BaseModel):
    """Schema for memory context returned by UnifiedMemoryManager."""

    session_id: str
    recent_messages: List[ChatMessageResponse]  # Short-term buffer
    conversation_summary: Optional[str] = None  # Rolling summary
    semantic_context: List[str] = []  # Retrieved similar conversation snippets
    total_messages: int = 0
    pdf_ids: List[int] = []


class ConversationSnippet(BaseModel):
    """Schema for conversation snippets stored in semantic memory."""

    session_id: str
    text: str
    timestamp: datetime
    message_count: int
    metadata: Optional[dict] = None
