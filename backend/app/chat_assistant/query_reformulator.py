from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import settings
from ..memory.schemas import ChatMessageResponse


class QueryReformulator:
    """
    Query reformulator that enhances user queries with conversation context.

    Uses LLM to reformulate queries by incorporating chat history and context.
    """

    def __init__(self, llm_model: str = None):
        """
        Initialize query reformulator.

        Args:
            llm_model: LLM model to use for reformulation
        """
        self.llm_model = llm_model or settings.llm_model

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=0.2,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

    def reformulate_query(
        self,
        original_query: str,
        recent_messages: List[ChatMessageResponse],
        conversation_summary: Optional[str] = None,
    ) -> str:
        """
        Reformulate user query with conversation context.

        Args:
            original_query: Original user query
            recent_messages: Recent conversation messages
            conversation_summary: Optional conversation summary

        Returns:
            Reformulated query string
        """
        # If no context, return original query
        if not recent_messages and not conversation_summary:
            return original_query

        # Build context prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            original_query, recent_messages, conversation_summary
        )

        # Call LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            reformulated = response.content.strip()

            # If reformulation failed or is empty, return original
            if not reformulated or len(reformulated) < 10:
                return original_query

            return reformulated

        except Exception as e:
            print(f"Query reformulation failed: {e}")
            return original_query

    def _build_system_prompt(self) -> str:
        """Build system prompt for query reformulation."""
        return """You are a query reformulation assistant for a tender document analysis system.

Your task is to reformulate user queries by incorporating relevant context from the conversation history.

Guidelines:
1. **Preserve all specific references**: If the query mentions page numbers, sections, clauses, items, or other specific references, keep them EXACTLY as stated
   - Example: "What page is that on?" → "What page contains the contractor qualification requirements?"

2. **Resolve pronouns and relative references**: Replace "it", "that", "this", "those", "these" with the actual subject from conversation history
   - Example: "Tell me more about it" → "Tell me more about the safety compliance requirements"

3. **Add context for vague follow-ups**: Enhance queries that depend on previous discussion
   - Example: "Is there a requirement for that?" → "Is there a requirement for ISO 9001 certification mentioned in section 2.3?"

4. **Keep standalone queries as-is**: If the query is already complete and self-contained, return it unchanged
   - Example: "What are the technical specifications in section 3.2?" → (keep as-is)

5. **Don't lose information**: Never remove or simplify specific details, numbers, or technical terms from the original query

6. Keep the reformulated query concise (1-3 sentences max)

Output ONLY the reformulated query, no explanations or metadata."""

    def _build_user_prompt(
        self,
        original_query: str,
        recent_messages: List[ChatMessageResponse],
        conversation_summary: Optional[str] = None,
    ) -> str:
        """Build user prompt with query and context."""
        parts = []

        # Add conversation summary if available
        if conversation_summary:
            parts.append(f"Conversation Summary:\n{conversation_summary}\n")

        # Add recent messages
        if recent_messages:
            parts.append("Recent Conversation:")
            for msg in recent_messages[-5:]:  # Last 5 messages max
                parts.append(f"{msg.role}: {msg.content}")
            parts.append("")

        # Add original query
        parts.append(f"User's New Query:\n{original_query}\n")

        parts.append("Reformulated Query:")

        return "\n".join(parts)

    def should_reformulate(
        self, query: str, recent_messages: List[ChatMessageResponse]
    ) -> bool:
        """
        Determine if query should be reformulated.

        Args:
            query: User query
            recent_messages: Recent messages

        Returns:
            True if reformulation would be beneficial
        """
        # Don't reformulate if no conversation context
        if not recent_messages or len(recent_messages) < 2:
            return False

        # Don't reformulate very short queries (likely greetings or yes/no)
        if len(query.split()) < 3:
            return False

        # Otherwise, let the LLM decide via system prompt
        # It will preserve specific references and only add context when needed
        return True
