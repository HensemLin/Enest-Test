from typing import List

import tiktoken
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import settings


class ShortTermMemory:
    """
    Short-term memory for managing recent conversation messages in-memory.

    Simplified approach:
    - Keeps recent messages in memory during session
    - Manual message trimming to keep buffer size manageable
    - Summarization support for long conversations
    - No persistence (uses long-term memory for that)
    """

    def __init__(
        self,
        max_tokens_before_summary: int = None,
        messages_to_keep: int = None,
        llm_model: str = None,
    ):
        """
        Initialize short-term memory.

        Args:
            max_tokens_before_summary: Maximum tokens before triggering summarization
            messages_to_keep: Number of recent messages to keep verbatim
            llm_model: LLM model to use for chat and summarization
        """
        self.max_tokens_before_summary = (
            max_tokens_before_summary or settings.memory_max_tokens
        )
        self.messages_to_keep = messages_to_keep or settings.memory_buffer_messages
        self.llm_model = llm_model or settings.llm_model

        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=0.3,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # In-memory message buffer (loaded from long-term on initialization)
        self._messages = []

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to short-term memory.

        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        if role == "user":
            self._messages.append(HumanMessage(content=content))
        elif role == "assistant":
            self._messages.append(AIMessage(content=content))
        else:
            raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

        # Trim old messages if buffer is too large
        if len(self._messages) > self.messages_to_keep * 2:
            self._messages = self._messages[-self.messages_to_keep :]

    def get_recent_messages(self, limit: int = None) -> List[dict]:
        """
        Get recent messages from buffer.

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with role and content
        """
        messages = self._messages
        if limit:
            messages = messages[-limit:]

        formatted_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            else:
                continue

            formatted_messages.append({"role": role, "content": msg.content})

        return formatted_messages

    def get_conversation_summary(self) -> str:
        """
        Generate a conversation summary using LLM.

        Returns:
            Summary string of the conversation so far
        """
        if len(self._messages) < 4:
            return ""

        conversation_text = self.get_buffer_string()

        token_count = self.count_tokens(conversation_text)
        if token_count < self.max_tokens_before_summary:
            return ""

        try:
            messages = [
                SystemMessage(
                    content="""You are a conversation summarizer. Create a concise summary of the conversation below.

Focus on:
- Main topics discussed
- Key questions asked
- Important information provided
- Any decisions or conclusions

Keep the summary brief (2-3 sentences) but informative."""
                ),
                HumanMessage(
                    content=f"Summarize this conversation:\n\n{conversation_text}"
                ),
            ]

            response = self.llm.invoke(messages)
            summary = response.content.strip()

            return summary
        except Exception as e:
            print(f"Warning: Failed to generate summary: {e}")
            return ""

    def get_buffer_string(self) -> str:
        """
        Get the buffer as a formatted string for LLM context.

        Returns:
            Formatted conversation string
        """
        messages = self.get_recent_messages()
        buffer_lines = []

        for msg in messages:
            prefix = "Human:" if msg["role"] == "user" else "AI:"
            buffer_lines.append(f"{prefix} {msg['content']}")

        return "\n".join(buffer_lines)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))

    def clear(self) -> None:
        """Clear all messages from short-term memory."""
        self._messages = []

    def load_from_messages(self, messages: List[dict]) -> None:
        """
        Load messages into memory from a list.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
        """
        self.clear()
        for msg in messages:
            self.add_message(msg["role"], msg["content"])

    def load_messages_batch(self, messages: List[dict]) -> None:
        """
        Efficiently load multiple messages at once.

        This method is optimized for bulk loading (e.g., from database during initialization).

        Args:
            messages: List of message dicts with 'role' and 'content' keys
        """
        for msg in messages:
            if msg["role"] == "user":
                self._messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                self._messages.append(AIMessage(content=msg["content"]))
            else:
                raise ValueError(
                    f"Invalid role: {msg['role']}. Must be 'user' or 'assistant'"
                )

    def get_memory_stats(self) -> dict:
        """
        Get statistics about current memory state.

        Note: This method does NOT generate a summary (expensive LLM call).
        Use get_conversation_summary() explicitly if you need to generate one.

        Returns:
            Dictionary with memory statistics
        """
        buffer_string = self.get_buffer_string()
        buffer_tokens = self.count_tokens(buffer_string)

        return {
            "total_messages": len(self._messages),
            "buffer_tokens": buffer_tokens,
            "max_token_limit": self.max_tokens_before_summary,
            "exceeds_token_limit": buffer_tokens >= self.max_tokens_before_summary,
        }
