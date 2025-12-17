from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from ..config import settings
from ..memory.long_term import LongTermMemory
from ..memory.memory_manager import UnifiedMemoryManager
from .query_reformulator import QueryReformulator
from .rag_engine import RAGEngine
from .schemas import ChatResponse, SourceDocument


class ChatAssistantService:
    """
    Chat assistant service integrating RAG + Memory + LLM.

    Orchestrates the complete conversational AI pipeline.
    """

    def __init__(self, db: Session):
        """
        Initialize chat assistant service.

        Args:
            db: Database session
        """
        self.db = db
        self.rag_engine = RAGEngine(db)
        self.query_reformulator = QueryReformulator()

        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.chat_temperature,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

        # Cache for memory managers (key: session_id, value: UnifiedMemoryManager)
        # Avoids recreating manager for every message in same session
        self._memory_manager_cache = {}
        self._max_cache_size = 50  # Maximum number of sessions to keep in cache

    def _get_or_create_memory_manager(
        self,
        session_id: str,
        pdf_ids: List[int],
        user_id: Optional[str] = None,
    ) -> UnifiedMemoryManager:
        """
        Get cached memory manager or create new one.

        Cache key includes both session_id and pdf_ids to ensure
        changing PDF selection creates a new manager.

        Args:
            session_id: Session identifier
            pdf_ids: List of PDF document IDs
            user_id: Optional user identifier

        Returns:
            UnifiedMemoryManager instance
        """
        # Create cache key from session_id + sorted pdf_ids
        # Sorted tuple for consistent key
        pdf_ids_key = tuple(sorted(pdf_ids))
        cache_key = f"{session_id}:{pdf_ids_key}"

        if cache_key in self._memory_manager_cache:
            return self._memory_manager_cache[cache_key]

        memory_manager = UnifiedMemoryManager(session_id, pdf_ids, self.db, user_id)

        self._memory_manager_cache[session_id] = memory_manager

        # Evict oldest entries if cache is full
        if len(self._memory_manager_cache) > self._max_cache_size:
            first_key = next(iter(self._memory_manager_cache))
            del self._memory_manager_cache[first_key]

        return memory_manager

    def process_chat_message(
        self,
        session_id: str,
        message: str,
        pdf_ids: List[int],
        user_id: Optional[str] = None,
        use_semantic_memory: bool = True,
    ) -> ChatResponse:
        """
        Process a chat message with RAG and memory integration.

        Args:
            session_id: Unique session identifier
            message: User message
            pdf_ids: List of PDF document IDs to search
            user_id: Optional user identifier
            use_semantic_memory: Whether to use semantic memory retrieval

        Returns:
            ChatResponse with assistant's reply and sources
        """
        memory_manager = self._get_or_create_memory_manager(
            session_id, pdf_ids, user_id
        )

        memory_manager.add_user_message(message)

        query_for_semantic = message if use_semantic_memory else None
        memory_context = memory_manager.get_memory_context(query=query_for_semantic)

        reformulated_query = message
        if self.query_reformulator.should_reformulate(
            message, memory_context.recent_messages
        ):
            reformulated_query = self.query_reformulator.reformulate_query(
                message,
                memory_context.recent_messages,
                memory_context.conversation_summary,
            )
            print(f"Reformulated query: {reformulated_query}", flush=True)

        # Retrieve docs using both original and reformulated queries for better recall
        retrieved_docs = self.rag_engine.retrieve_relevant_chunks(
            reformulated_query, pdf_ids, top_k=10
        )

        # If query was reformulated, also search with original query and merge results
        if reformulated_query != message:
            original_results = self.rag_engine.retrieve_relevant_chunks(
                message, pdf_ids, top_k=5
            )
            # Merge and deduplicate by document content
            seen_contents = {doc.page_content for doc, _ in retrieved_docs}
            for doc, score in original_results:
                if doc.page_content not in seen_contents:
                    retrieved_docs.append((doc, score))
                    seen_contents.add(doc.page_content)

            retrieved_docs.sort(key=lambda x: x[1])

            retrieved_docs = retrieved_docs[:10]
            print(f"Merged results from original query: '{message}'", flush=True)

        # Log retrieved documents
        print(f"\n{'='*80}", flush=True)
        print(
            f"RETRIEVED {len(retrieved_docs)} DOCUMENTS FROM PDFs: {pdf_ids}",
            flush=True,
        )
        print(f"{'='*80}", flush=True)
        for idx, (doc, score) in enumerate(retrieved_docs, 1):
            print(f"\nDocument {idx}:", flush=True)
            print(f"  PDF ID: {doc.metadata.get('pdf_id', 'N/A')}", flush=True)
            print(f"  Page: {doc.metadata.get('page_number', 'N/A')}", flush=True)
            print(f"  Score: {score:.4f}", flush=True)
            print(f"  Text preview: {doc.page_content[:200]}...", flush=True)
        print(f"{'='*80}\n", flush=True)

        document_context = self.rag_engine.format_retrieved_context(retrieved_docs)

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(message, document_context, memory_context)

        # Log the prompts being sent to LLM
        print("\n" + "=" * 80, flush=True)
        print("SYSTEM PROMPT:", flush=True)
        print("=" * 80, flush=True)
        print(system_prompt, flush=True)
        print("\n" + "=" * 80, flush=True)
        print("USER PROMPT:", flush=True)
        print("=" * 80, flush=True)
        print(user_prompt, flush=True)
        print("=" * 80 + "\n", flush=True)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            llm_response = self.llm.invoke(messages)
            assistant_message = llm_response.content.strip()

            # Log LLM response
            print("\n" + "=" * 80, flush=True)
            print("LLM RESPONSE:", flush=True)
            print("=" * 80, flush=True)
            print(assistant_message, flush=True)
            print("=" * 80 + "\n", flush=True)
        except Exception as e:
            print(f"LLM invocation failed: {e}")
            assistant_message = "I apologize, but I encountered an error processing your request. Please try again."

        sources = self.rag_engine.get_source_references(retrieved_docs)

        memory_manager.add_assistant_message(assistant_message, sources)

        memory_stats = memory_manager.get_memory_stats()

        return ChatResponse(
            session_id=session_id,
            message=assistant_message,
            sources=[SourceDocument(**src) for src in sources],
            conversation_summary=memory_context.conversation_summary,
            total_messages=memory_stats["total_messages"],
            memory_stats=memory_stats,
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for the chat assistant."""
        return """You are an intelligent tender document analysis assistant.

Your role is to help users understand and analyze tender documents, including:
- Technical specifications and requirements
- Bill of Materials (BoM) and Bill of Quantities (BoQ)
- Compliance criteria and mandatory requirements
- Project timelines and deliverables
- Vendor qualifications and submission guidelines

Guidelines:
1. Provide accurate, concise answers based on the provided document context
2. Always cite specific document references (page numbers, sections) when answering
3. If information is not found in the documents, clearly state that
4. For complex questions, break down your answer into clear sections
5. Highlight mandatory vs. optional requirements when relevant
6. Be professional and precise in your language
7. If a question is ambiguous, ask for clarification

Remember: Your responses should be grounded in the provided document excerpts."""

    def _build_user_prompt(
        self, user_query: str, document_context: str, memory_context
    ) -> str:
        """Build user prompt with all context."""
        parts = []

        # Add conversation summary if available
        if memory_context.conversation_summary:
            parts.append("=== Conversation Summary ===")
            parts.append(memory_context.conversation_summary)
            parts.append("")

        # Add semantic context if available
        if memory_context.semantic_context:
            parts.append("=== Relevant Past Discussion ===")
            for idx, snippet in enumerate(memory_context.semantic_context, 1):
                parts.append(f"{idx}. {snippet}")
            parts.append("")

        # Add document context
        parts.append("=== Document Context ===")
        parts.append(document_context)
        parts.append("")

        # Add recent messages for immediate context
        if memory_context.recent_messages:
            parts.append("=== Recent Conversation ===")
            for msg in memory_context.recent_messages[-3:]:  # Last 3 messages
                parts.append(f"{msg.role}: {msg.content}")
            parts.append("")

        # Add current user query
        parts.append("=== User Question ===")
        parts.append(user_query)
        parts.append("")
        parts.append("Your Answer:")

        return "\n".join(parts)

    def get_session_info(self, session_id: str) -> dict:
        """
        Get session information and memory stats.

        Args:
            session_id: Session identifier

        Returns:
            Session information dictionary
        """
        long_term = LongTermMemory(self.db)
        session = long_term.get_session(session_id)

        if not session:
            return None

        return {
            "session_id": session.session_id,
            "pdf_ids": session.pdf_ids,
            "user_id": session.user_id,
            "total_messages": session.total_messages,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "summary": session.summary,
        }

    def get_all_sessions(
        self, user_id: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """
        Get all chat sessions.

        Args:
            user_id: Optional user filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of session dictionaries
        """
        long_term = LongTermMemory(self.db)
        sessions = long_term.get_all_sessions(user_id=user_id, skip=skip, limit=limit)

        return [
            {
                "id": session.id,
                "session_id": session.session_id,
                "pdf_ids": session.pdf_ids,
                "user_id": session.user_id,
                "total_messages": session.total_messages,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "summary": session.summary,
            }
            for session in sessions
        ]

    def get_session_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> List[dict]:
        """
        Get messages for a specific session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries
        """
        long_term = LongTermMemory(self.db)
        messages = long_term.get_messages(session_id, limit=limit)

        return [
            {
                "id": msg.id,
                "session_id": msg.session_id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "sources": msg.sources,
                "token_count": msg.token_count,
            }
            for msg in messages
        ]
