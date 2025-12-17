from typing import List, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Schema for chat request."""

    session_id: str
    message: str
    pdf_ids: List[int]
    user_id: Optional[str] = None
    use_semantic_memory: bool = True


class SourceDocument(BaseModel):
    """Schema for source document reference."""

    pdf_id: int
    pdf_filename: Optional[str] = None
    page_number: int
    chunk_index: int
    text_snippet: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Schema for chat response."""

    session_id: str
    message: str
    sources: List[SourceDocument] = []
    conversation_summary: Optional[str] = None
    total_messages: int = 0
    memory_stats: Optional[dict] = None


class SessionInfoRequest(BaseModel):
    """Schema for session info request."""

    session_id: str


class SessionInfoResponse(BaseModel):
    """Schema for session information response."""

    session_id: str
    pdf_ids: List[int]
    user_id: Optional[str] = None
    total_messages: int
    created_at: str
    last_activity: str
    summary: Optional[str] = None
    memory_stats: Optional[dict] = None
