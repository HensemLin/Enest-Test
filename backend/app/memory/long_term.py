from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from .models import ChatMessage, ChatSession
from .schemas import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate


class LongTermMemory:
    """
    Long-term memory using PostgreSQL for persistent storage.

    Stores all chat sessions and messages for retrieval and analysis.
    """

    def __init__(self, db: Session):
        """
        Initialize long-term memory with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_session(self, session_data: ChatSessionCreate) -> ChatSession:
        """
        Create a new chat session.

        Args:
            session_data: Session creation data

        Returns:
            Created ChatSession object
        """
        session = ChatSession(
            session_id=session_data.session_id,
            pdf_ids=session_data.pdf_ids,
            user_id=session_data.user_id,
            total_messages=0,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Retrieve a chat session by ID.

        Args:
            session_id: Unique session identifier

        Returns:
            ChatSession object or None if not found
        """
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.session_id == session_id)
            .first()
        )

    def get_or_create_session(
        self, session_id: str, pdf_ids: List[int], user_id: Optional[str] = None
    ) -> ChatSession:
        """
        Get existing session or create new one.

        Args:
            session_id: Unique session identifier
            pdf_ids: List of PDF document IDs
            user_id: Optional user identifier

        Returns:
            ChatSession object
        """
        session = self.get_session(session_id)
        if not session:
            session_data = ChatSessionCreate(
                session_id=session_id, pdf_ids=pdf_ids, user_id=user_id
            )
            session = self.create_session(session_data)
        return session

    def update_session(
        self, session_id: str, update_data: ChatSessionUpdate
    ) -> ChatSession:
        """
        Update chat session metadata.

        Args:
            session_id: Session to update
            update_data: Update data

        Returns:
            Updated ChatSession object
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if update_data.summary is not None:
            session.summary = update_data.summary
        if update_data.total_messages is not None:
            session.total_messages = update_data.total_messages
        if update_data.session_metadata is not None:
            session.session_metadata = update_data.session_metadata

        # Update last_activity timestamp
        session.last_activity = datetime.now()

        self.db.commit()
        self.db.refresh(session)
        return session

    def add_message(self, message_data: ChatMessageCreate, session: ChatSession) -> ChatMessage:
        """
        Add a message to the database.

        Args:
            message_data: Message creation data
            session: ChatSession object to update (passed by reference, will be updated in-place)

        Returns:
            Created ChatMessage object
        """
        message = ChatMessage(
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content,
            sources=message_data.sources,
            token_count=message_data.token_count,
        )
        self.db.add(message)

        # Increment total_messages counter in provided session (no DB query needed)
        session.total_messages += 1
        session.last_activity = datetime.now()

        self.db.commit()
        self.db.refresh(message)
        self.db.refresh(session)  # Refresh session to sync with committed DB state
        return message

    def get_messages(
        self, session_id: str, limit: Optional[int] = None, offset: int = 0
    ) -> List[ChatMessage]:
        """
        Retrieve messages for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip

        Returns:
            List of ChatMessage objects ordered by timestamp
        """
        query = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp)
        )

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_recent_messages(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """
        Get most recent messages for a session.

        Args:
            session_id: Session identifier
            limit: Number of recent messages to retrieve

        Returns:
            List of recent ChatMessage objects
        """
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.timestamp))
            .limit(limit)
            .all()
        )
        # Reverse to get chronological order
        return list(reversed(messages))

    def get_message_count(self, session_id: str) -> int:
        """
        Get total number of messages in a session.

        Args:
            session_id: Session identifier

        Returns:
            Message count
        """
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .count()
        )

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session and all its messages (CASCADE).

        Args:
            session_id: Session to delete

        Returns:
            True if successful
        """
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False

    def get_all_sessions(
        self, user_id: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[ChatSession]:
        """
        Get all chat sessions, optionally filtered by user.

        Args:
            user_id: Optional user filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of ChatSession objects
        """
        query = self.db.query(ChatSession).order_by(desc(ChatSession.last_activity))

        if user_id:
            query = query.filter(ChatSession.user_id == user_id)

        return query.offset(skip).limit(limit).all()
