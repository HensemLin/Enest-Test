import re
from typing import List, Optional

import fitz
import pymupdf4llm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFTextExtractor:
    """Extract and chunk text from PDF documents using PyMuPDF."""

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 300,
        separators: Optional[List[str]] = None,
    ):
        """
        Initialize text extractor with chunking parameters.

        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Overlap between consecutive chunks
            separators: Custom separators for text splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Default separators for tender documents (preserve structure)
        if separators is None:
            separators = [
                "\n\n\n",  # Multiple newlines (section breaks)
                "\n\n",  # Paragraph breaks
                "\n",  # Line breaks
                ". ",  # Sentence breaks
                ", ",  # Clause breaks
                " ",  # Word breaks
                "",  # Character breaks
            ]

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def extract_text_from_pdf(
        self, pdf_path: str, use_markdown: bool = False
    ) -> List[dict]:
        """
        Extract text from PDF page by page.

        Args:
            pdf_path: Path to PDF file
            use_markdown: If True, extract as markdown with structure; if False, extract as plain text

        Returns:
            List of dictionaries with page number and text/markdown content
        """
        if use_markdown:
            # Use pymupdf4llm for markdown extraction (preserves structure)
            md_pages = pymupdf4llm.to_markdown(
                pdf_path, page_chunks=True, write_images=False, show_progress=False
            )

            pages = []
            for page_data in md_pages:
                pages.append(
                    {
                        "page_number": page_data["metadata"]["page"] + 1,
                        "text": page_data["text"],
                        "char_count": len(page_data["text"]),
                        "method": "markdown",
                    }
                )
            return pages
        else:
            # Use plain text extraction (original behavior)
            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")

                text = self._clean_text(text)

                pages.append(
                    {
                        "page_number": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                        "method": "plain_text",
                    }
                )

            doc.close()
            return pages

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing excessive whitespace and page headers/footers."""
        # Remove common page header patterns (match multiple lines)
        text = re.sub(
            r'FOR TENDER PURPOSE[^\n]*\n[^\n]*OF\s*\d+',
            '',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )

        # Remove standalone page numbers
        text = re.sub(r'^\s*\d+\s*OF\s*\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        lines = [line.rstrip() for line in text.split("\n")]
        text = "\n".join(lines)

        return text.strip()

    def extract_and_chunk(
        self,
        pdf_path: str,
        pdf_id: int,
        include_metadata: bool = True,
        use_markdown: bool = False,
    ) -> List[Document]:
        """
        Extract text from PDF and split into chunks for vector storage.

        Args:
            pdf_path: Path to PDF file
            pdf_id: Database ID of PDF document
            include_metadata: Whether to include page numbers and PDF ID in metadata
            use_markdown: If True, extract as markdown; if False, extract as plain text

        Returns:
            List of LangChain Document objects with text chunks and metadata
        """
        pages = self.extract_text_from_pdf(pdf_path, use_markdown=use_markdown)

        # Create Document objects for each page
        documents = []
        for page_data in pages:
            if page_data["text"].strip():
                metadata = (
                    {
                        "pdf_id": pdf_id,
                        "page_number": page_data["page_number"],
                        "source": pdf_path,
                    }
                    if include_metadata
                    else {}
                )

                doc = Document(page_content=page_data["text"], metadata=metadata)
                documents.append(doc)

        chunked_docs = self.text_splitter.split_documents(documents)

        # Filter out useless chunks (too short or only boilerplate)
        filtered_chunks = []
        for doc in chunked_docs:
            content = doc.page_content.strip()

            # Skip if chunk is too short (less than 100 chars)
            if len(content) < 100:
                continue

            # Skip if chunk is mostly just numbers/dots/whitespace (like index pages)
            if re.match(r'^[\d\s.…\-–]+$', content):
                continue

            # Skip if chunk contains only section numbers with no content
            if re.match(r'^(\d+\.)+\s*$', content):
                continue

            filtered_chunks.append(doc)

        # Update chunk indices after filtering
        for idx, doc in enumerate(filtered_chunks):
            doc.metadata["chunk_index"] = idx
            doc.metadata["total_chunks"] = len(filtered_chunks)

        return filtered_chunks

    def get_page_text(self, pdf_path: str, page_number: int) -> str:
        """
        Get text from a specific page.

        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)

        Returns:
            Text content of the page
        """
        doc = fitz.open(pdf_path)
        if page_number < 1 or page_number > len(doc):
            doc.close()
            raise ValueError(f"Invalid page number: {page_number}")

        page = doc[page_number - 1]
        text = page.get_text("text")
        doc.close()

        return self._clean_text(text)

    def search_text_in_pdf(self, pdf_path: str, query: str) -> List[dict]:
        """
        Search for text in PDF and return matching pages.

        Args:
            pdf_path: Path to PDF file
            query: Search query

        Returns:
            List of dictionaries with page numbers and matching text snippets
        """
        doc = fitz.open(pdf_path)
        results = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")

            # Case-insensitive search
            if query.lower() in text.lower():
                # Find context around match
                idx = text.lower().find(query.lower())
                start = max(0, idx - 100)
                end = min(len(text), idx + len(query) + 100)
                snippet = text[start:end].strip()

                results.append(
                    {"page_number": page_num + 1, "snippet": snippet, "full_text": text}
                )

        doc.close()
        return results
