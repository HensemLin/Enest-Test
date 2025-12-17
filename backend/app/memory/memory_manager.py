from typing import List, Optional

from sqlalchemy.orm import Session

from ..config import settings
from .long_term import LongTermMemory
from .schemas import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionUpdate,
    MemoryContext,
)
from .semantic_memory import SemanticMemory
from .short_term import ShortTermMemory


class UnifiedMemoryManager:
    """
    Unified memory manager orchestrating 3-tier hybrid memory system:
    1. Short-term: LangGraph with PostgresSaver (recent messages + checkpointing)
    2. Long-term: PostgreSQL (all messages persisted)
    3. Semantic: FAISS vector store (semantic similarity search)
    """

    def __init__(
        self,
        session_id: str,
        pdf_ids: List[int],
        db: Session,
        user_id: Optional[str] = None,
    ):
        """
        Initialize unified memory manager.

        Args:
            session_id: Unique session identifier
            pdf_ids: List of PDF document IDs for this conversation
            db: SQLAlchemy database session
            user_id: Optional user identifier
        """
        self.session_id = session_id
        self.pdf_ids = pdf_ids
        self.user_id = user_id

        # Initialize three memory tiers
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(db)
        self.semantic = SemanticMemory(session_id)

        # Get or create session
        self.session = self.long_term.get_or_create_session(
            session_id, pdf_ids, user_id
        )

        # Load recent messages from database into short-term memory
        self._initialize_short_term_from_db()

    def _initialize_short_term_from_db(self) -> None:
        """Load recent messages from database into short-term memory."""
        recent_messages = self.long_term.get_recent_messages(
            self.session_id, limit=settings.memory_buffer_messages
        )

        # Load into short-term memory using batch method (efficient - only 1 checkpoint save)
        messages_to_load = [
            {"role": msg.role, "content": msg.content} for msg in recent_messages
        ]
        if messages_to_load:
            self.short_term.load_messages_batch(messages_to_load)

    def add_user_message(self, content: str) -> ChatMessageResponse:
        """
        Add a user message to all memory tiers.

        Args:
            content: User message content

        Returns:
            Created message response
        """
        # Add to short-term memory
        self.short_term.add_message("user", content)

        # Persist to long-term memory (session updated by reference inside add_message)
        message_data = ChatMessageCreate(
            session_id=self.session_id, role="user", content=content
        )
        message = self.long_term.add_message(message_data, self.session)

        # Check if we should trigger summarization
        self._check_and_update_summary()

        return ChatMessageResponse.model_validate(message)

    def add_assistant_message(
        self, content: str, sources: Optional[List[dict]] = None
    ) -> ChatMessageResponse:
        """
        Add an assistant message to all memory tiers.

        Args:
            content: Assistant message content
            sources: Optional source documents/chunks

        Returns:
            Created message response
        """
        self.short_term.add_message("assistant", content)

        message_data = ChatMessageCreate(
            session_id=self.session_id,
            role="assistant",
            content=content,
            sources=sources,
        )
        message = self.long_term.add_message(message_data, self.session)

        # Add to semantic memory (every 2-3 exchanges)
        total_messages = self.session.total_messages
        if total_messages % 4 == 0:  # Every 2 exchanges (4 messages)
            self._add_to_semantic_memory()

        self._check_and_update_summary()

        return ChatMessageResponse.model_validate(message)

    def _check_and_update_summary(self) -> None:
        """Check if summarization should be triggered and update session summary."""
        total_messages = self.session.total_messages

        if (
            total_messages >= settings.memory_summary_trigger
            and total_messages % settings.memory_summary_trigger == 0
        ):
            summary = self.short_term.get_conversation_summary()
            if summary:
                update_data = ChatSessionUpdate(summary=summary)
                updated_session = self.long_term.update_session(
                    self.session_id, update_data
                )
                self.session = updated_session

    def _add_to_semantic_memory(self) -> None:
        """Add recent conversation exchange to semantic memory."""
        # Get last 4 messages (2 exchanges)
        recent_messages = self.short_term.get_recent_messages(limit=4)

        if len(recent_messages) >= 2:
            snippet_text = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
            )

            metadata = {
                "session_id": self.session_id,
                "message_count": len(recent_messages),
                "total_messages": self.session.total_messages,
            }
            self.semantic.add_conversation_snippet(snippet_text, metadata)

    def get_memory_context(self, query: Optional[str] = None) -> MemoryContext:
        """
        Get comprehensive memory context for query.

        Args:
            query: Optional query for semantic retrieval

        Returns:
            MemoryContext with all memory tiers
        """
        recent_messages_from_db = self.long_term.get_recent_messages(
            self.session_id, limit=settings.memory_buffer_messages
        )

        recent_messages = [
            ChatMessageResponse.model_validate(msg) for msg in recent_messages_from_db
        ]

        summary = self.session.summary

        semantic_context = []
        if query:
            semantic_context = self.semantic.retrieve_similar_context(query)

        return MemoryContext(
            session_id=self.session_id,
            recent_messages=recent_messages,
            conversation_summary=summary,
            semantic_context=semantic_context,
            total_messages=self.session.total_messages,
            pdf_ids=self.pdf_ids,
        )

    def get_formatted_context_string(self, query: Optional[str] = None) -> str:
        """
        Get formatted context string for LLM prompt.

        Args:
            query: Optional query for semantic retrieval

        Returns:
            Formatted context string
        """
        context = self.get_memory_context(query)

        parts = []

        if context.conversation_summary:
            parts.append(f"Conversation Summary:\n{context.conversation_summary}\n")

        if context.semantic_context:
            parts.append("Relevant Past Context:")
            for idx, snippet in enumerate(context.semantic_context, 1):
                parts.append(f"{idx}. {snippet}")
            parts.append("")

        if context.recent_messages:
            parts.append("Recent Messages:")
            for msg in context.recent_messages:
                parts.append(f"{msg.role}: {msg.content}")

        return "\n".join(parts)

    def clear_session(self) -> None:
        """Clear all memory for this session."""
        self.short_term.clear()
        self.semantic.clear()
        self.long_term.delete_session(self.session_id)

    def get_memory_stats(self) -> dict:
        """
        Get statistics about all memory tiers.

        Returns:
            Dictionary with memory statistics
        """
        short_term_stats = self.short_term.get_memory_stats()
        semantic_doc_count = self.semantic.get_document_count()
        long_term_count = self.long_term.get_message_count(self.session_id)

        return {
            "session_id": self.session_id,
            "pdf_ids": self.pdf_ids,
            "total_messages": self.session.total_messages,
            "short_term": short_term_stats,
            "long_term_messages": long_term_count,
            "semantic_snippets": semantic_doc_count,
            "has_summary": bool(self.session.summary),
        }
