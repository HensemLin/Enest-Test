import os
import shutil
from pathlib import Path
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from ..config import settings


class SemanticMemory:
    """
    Semantic memory using FAISS vector store.

    Stores conversation snippets as embeddings for semantic similarity search.
    Enables retrieving relevant past conversation context.
    """

    def __init__(
        self,
        session_id: str,
        embedding_model: str = None,
        top_k: int = None,
    ):
        """
        Initialize semantic memory with FAISS vector store.

        Args:
            session_id: Unique session identifier for this memory instance
            embedding_model: Model to use for embeddings
            top_k: Number of top results to retrieve
        """
        self.session_id = session_id
        self.embedding_model = embedding_model or settings.embedding_model
        self.top_k = top_k or settings.semantic_memory_top_k

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

        # Vector store path
        self.vector_store_path = os.path.join(
            settings.vector_storage_path, f"session_{session_id}"
        )
        Path(settings.vector_storage_path).mkdir(parents=True, exist_ok=True)

        # Load or initialize vector store
        self.vector_store = self._load_or_create_vector_store()

    def _load_or_create_vector_store(self) -> Optional[FAISS]:
        """
        Load existing vector store or return None.

        Returns:
            FAISS vector store or None if doesn't exist
        """
        if os.path.exists(self.vector_store_path):
            try:
                return FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
            except Exception as e:
                print(f"Failed to load vector store: {e}")
                return None
        return None

    def add_conversation_snippet(
        self, text: str, metadata: Optional[dict] = None
    ) -> None:
        """
        Add a conversation snippet to semantic memory.

        Args:
            text: Conversation text to store
            metadata: Optional metadata (timestamp, message_count, etc.)
        """
        if not text.strip():
            return

        # Create document
        doc = Document(
            page_content=text,
            metadata=metadata or {"session_id": self.session_id},
        )

        # Add to vector store
        if self.vector_store is None:
            # Create new vector store
            self.vector_store = FAISS.from_documents([doc], self.embeddings)
        else:
            # Add to existing vector store
            self.vector_store.add_documents([doc])

        # Save to disk
        self._save_vector_store()

    def add_multiple_snippets(self, snippets: List[dict]) -> None:
        """
        Add multiple conversation snippets at once.

        Args:
            snippets: List of dicts with 'text' and optional 'metadata' keys
        """
        if not snippets:
            return

        documents = []
        for snippet in snippets:
            if snippet.get("text", "").strip():
                metadata = snippet.get("metadata", {})
                metadata["session_id"] = self.session_id
                doc = Document(page_content=snippet["text"], metadata=metadata)
                documents.append(doc)

        if not documents:
            return

        # Add documents
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
        else:
            self.vector_store.add_documents(documents)

        # Save to disk
        self._save_vector_store()

    def retrieve_similar_context(
        self, query: str, top_k: Optional[int] = None
    ) -> List[str]:
        """
        Retrieve semantically similar conversation snippets.

        Args:
            query: Query text to search for
            top_k: Number of results to return (uses default if not specified)

        Returns:
            List of relevant conversation snippets
        """
        if self.vector_store is None:
            return []

        k = top_k or self.top_k

        try:
            # Perform similarity search
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"Error retrieving semantic context: {e}")
            return []

    def retrieve_with_scores(
        self, query: str, top_k: Optional[int] = None
    ) -> List[tuple[str, float]]:
        """
        Retrieve similar snippets with similarity scores.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            List of tuples (snippet_text, similarity_score)
        """
        if self.vector_store is None:
            return []

        k = top_k or self.top_k

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [(doc.page_content, score) for doc, score in results]
        except Exception as e:
            print(f"Error retrieving semantic context: {e}")
            return []

    def _save_vector_store(self) -> None:
        """Save vector store to disk."""
        if self.vector_store is not None:
            try:
                self.vector_store.save_local(self.vector_store_path)
            except Exception as e:
                print(f"Failed to save vector store: {e}")

    def clear(self) -> None:
        """Clear all semantic memory for this session."""
        self.vector_store = None
        if os.path.exists(self.vector_store_path):
            shutil.rmtree(self.vector_store_path)

    def get_document_count(self) -> int:
        """
        Get number of documents in vector store.

        Returns:
            Document count
        """
        if self.vector_store is None:
            return 0
        return self.vector_store.index.ntotal

    @staticmethod
    def delete_session_memory(session_id: str) -> bool:
        """
        Delete semantic memory for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        vector_store_path = os.path.join(
            settings.vector_storage_path, f"session_{session_id}"
        )
        if os.path.exists(vector_store_path):
            shutil.rmtree(vector_store_path)
            return True
        return False
