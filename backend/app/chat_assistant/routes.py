from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..common.middleware import verify_api_key_middleware
from ..database import get_db
from .schemas import ChatRequest, ChatResponse, SessionInfoRequest, SessionInfoResponse
from .service import ChatAssistantService

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat Assistant"],
    dependencies=[Depends(verify_api_key_middleware)],
)


def get_chat_service(db: Session = Depends(get_db)) -> ChatAssistantService:
    """Dependency to get ChatAssistantService instance."""
    return ChatAssistantService(db)


@router.post("/message", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest, service: ChatAssistantService = Depends(get_chat_service)
):
    """
    Send a chat message and get AI assistant response.

    Args:
        request: Chat request with session_id, message, and pdf_ids

    Returns:
        ChatResponse with assistant's reply and source documents
    """
    try:
        response = service.process_chat_message(
            session_id=request.session_id,
            message=request.message,
            pdf_ids=request.pdf_ids,
            user_id=request.user_id,
            use_semantic_memory=request.use_semantic_memory,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process chat message: {str(e)}"
        )


@router.post("/session/info", response_model=SessionInfoResponse)
async def get_session_info(
    request: SessionInfoRequest,
    service: ChatAssistantService = Depends(get_chat_service),
):
    """
    Get information about a chat session.

    Args:
        request: Session info request with session_id

    Returns:
        SessionInfoResponse with session details and memory stats
    """
    session_info = service.get_session_info(request.session_id)
    print(f"{request.session_id=}")
    if not session_info:
        raise HTTPException(
            status_code=404, detail=f"Session {request.session_id} not found"
        )

    return SessionInfoResponse(**session_info)


@router.get("/sessions")
async def get_all_sessions(
    user_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ChatAssistantService = Depends(get_chat_service),
):
    """
    Get all chat sessions.

    Args:
        user_id: Optional user filter
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return

    Returns:
        List of chat sessions with details
    """
    try:
        sessions = service.get_all_sessions(user_id=user_id, skip=skip, limit=limit)
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.get("/messages/{session_id}")
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1),
    service: ChatAssistantService = Depends(get_chat_service),
):
    """
    Get all messages for a specific session.

    Args:
        session_id: Session identifier
        limit: Optional limit on number of messages

    Returns:
        List of messages in the session
    """
    try:
        messages = service.get_session_messages(session_id, limit=limit)
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch messages: {str(e)}"
        )
