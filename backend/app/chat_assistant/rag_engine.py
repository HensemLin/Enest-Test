import os
import shutil
from typing import List, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session

from ..config import settings
from ..pdf_processing.service import PDFService
from ..pdf_processing.text_extractor import PDFTextExtractor


class RAGEngine:
    """
    RAG (Retrieval Augmented Generation) engine for document retrieval.

    Manages vector stores for PDF documents and performs semantic search.
    """

    def __init__(self, db: Session):
        """
        Initialize RAG engine.

        Args:
            db: Database session
        """
        self.db = db
        self.pdf_service = PDFService(db)
        self.text_extractor = PDFTextExtractor()

        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

        self.vector_store_cache = {}

    def _get_vector_store_path(self, pdf_id: int) -> str:
        """Get vector store path for a PDF."""
        return os.path.join(settings.vector_storage_path, f"pdf_{pdf_id}")

    def _load_or_create_vector_store(self, pdf_id: int) -> FAISS:
        """
        Load existing vector store or create new one from PDF.

        Args:
            pdf_id: PDF document ID

        Returns:
            FAISS vector store
        """
        if pdf_id in self.vector_store_cache:
            return self.vector_store_cache[pdf_id]

        vector_store_path = self._get_vector_store_path(pdf_id)

        if os.path.exists(vector_store_path):
            try:
                vector_store = FAISS.load_local(
                    vector_store_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                self.vector_store_cache[pdf_id] = vector_store
                return vector_store
            except Exception as e:
                print(f"Failed to load vector store for PDF {pdf_id}: {e}")

        return self._create_vector_store_from_pdf(pdf_id)

    def _create_vector_store_from_pdf(self, pdf_id: int) -> FAISS:
        """
        Create vector store from PDF document.

        Args:
            pdf_id: PDF document ID

        Returns:
            FAISS vector store
        """
        pdf_path = self.pdf_service.get_pdf_file_path(pdf_id)

        documents = self.text_extractor.extract_and_chunk(
            pdf_path, pdf_id, include_metadata=True
        )

        if not documents:
            raise ValueError(f"No text extracted from PDF {pdf_id}")

        vector_store = FAISS.from_documents(documents, self.embeddings)

        vector_store_path = self._get_vector_store_path(pdf_id)
        os.makedirs(os.path.dirname(vector_store_path), exist_ok=True)
        vector_store.save_local(vector_store_path)

        self.vector_store_cache[pdf_id] = vector_store

        return vector_store

    def retrieve_relevant_chunks(
        self, query: str, pdf_ids: List[int], top_k: int = 5
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: Search query
            pdf_ids: List of PDF IDs to search
            top_k: Number of top results to retrieve per PDF

        Returns:
            List of tuples (Document, relevance_score)
        """
        all_results = []

        for pdf_id in pdf_ids:
            try:
                vector_store = self._load_or_create_vector_store(pdf_id)

                results = vector_store.similarity_search_with_score(query, k=top_k)
                all_results.extend(results)

            except Exception as e:
                print(f"Error retrieving from PDF {pdf_id}: {e}")
                continue

        # Sort by relevance score (lower is better for FAISS)
        all_results.sort(key=lambda x: x[1])

        return all_results[: top_k * len(pdf_ids)]

    def format_retrieved_context(
        self, retrieved_docs: List[Tuple[Document, float]]
    ) -> str:
        """
        Format retrieved documents into context string for LLM.

        Args:
            retrieved_docs: List of (Document, score) tuples

        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return "No relevant context found in the documents."

        context_parts = ["Relevant Document Excerpts:\n"]

        pdf_cache = {}

        for idx, (doc, score) in enumerate(retrieved_docs, 1):
            metadata = doc.metadata
            pdf_id = metadata.get("pdf_id", "Unknown")
            page_num = metadata.get("page_number", "Unknown")

            pdf_display = f"PDF {pdf_id}"
            if pdf_id != "Unknown" and isinstance(pdf_id, int):
                if pdf_id not in pdf_cache:
                    try:
                        pdf_doc = self.pdf_service.get_pdf_by_id(pdf_id)
                        pdf_cache[pdf_id] = pdf_doc.original_filename
                    except Exception as e:
                        print(f"Warning: Could not fetch PDF {pdf_id}: {e}")
                        pdf_cache[pdf_id] = None

                if pdf_cache[pdf_id]:
                    pdf_display = pdf_cache[pdf_id]

            context_parts.append(
                f"{idx}. [{pdf_display}, Page {page_num}] (Relevance: {score:.3f})"
            )
            context_parts.append(f"{doc.page_content}\n")

        return "\n".join(context_parts)

    def get_source_references(
        self, retrieved_docs: List[Tuple[Document, float]]
    ) -> List[dict]:
        """
        Extract source references from retrieved documents.

        Args:
            retrieved_docs: List of (Document, score) tuples

        Returns:
            List of source reference dictionaries
        """
        sources = []
        pdf_cache = {}

        for doc, score in retrieved_docs:
            metadata = doc.metadata
            pdf_id = metadata.get("pdf_id")

            pdf_filename = None
            if pdf_id:
                if pdf_id not in pdf_cache:
                    try:
                        pdf_doc = self.pdf_service.get_pdf_by_id(pdf_id)
                        pdf_cache[pdf_id] = pdf_doc.original_filename
                    except Exception as e:
                        print(f"Warning: Could not fetch PDF {pdf_id}: {e}")
                        pdf_cache[pdf_id] = None
                pdf_filename = pdf_cache[pdf_id]

            source = {
                "pdf_id": pdf_id,
                "pdf_filename": pdf_filename,
                "page_number": metadata.get("page_number"),
                "chunk_index": metadata.get("chunk_index"),
                "text_snippet": doc.page_content[:200] + "...",
                "relevance_score": float(score),
            }
            sources.append(source)

        return sources

    def clear_vector_store_cache(self) -> None:
        """Clear the vector store cache."""
        self.vector_store_cache.clear()

    def delete_vector_store(self, pdf_id: int) -> bool:
        """
        Delete vector store for a specific PDF.

        Args:
            pdf_id: PDF document ID

        Returns:
            True if successful
        """
        vector_store_path = self._get_vector_store_path(pdf_id)

        if os.path.exists(vector_store_path):
            shutil.rmtree(vector_store_path)

            if pdf_id in self.vector_store_cache:
                del self.vector_store_cache[pdf_id]

            return True
        return False

    def rebuild_vector_store(self, pdf_id: int) -> FAISS:
        """
        Rebuild vector store for a PDF (useful if PDF was updated).

        Args:
            pdf_id: PDF document ID

        Returns:
            New FAISS vector store
        """
        self.delete_vector_store(pdf_id)

        return self._create_vector_store_from_pdf(pdf_id)
