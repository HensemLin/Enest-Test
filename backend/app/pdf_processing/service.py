import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from .models import PDFDocument


class PDFService:
    """Service for handling PDF upload, storage, and metadata extraction."""

    def __init__(self, db: Session):
        self.db = db
        self._ensure_storage_dirs()

    def _ensure_storage_dirs(self):
        """Create storage directories if they don't exist."""
        Path(settings.pdf_storage_path).mkdir(parents=True, exist_ok=True)
        Path(settings.processed_storage_path).mkdir(parents=True, exist_ok=True)

    def _validate_pdf(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only {', '.join(settings.allowed_extensions)} allowed.",
            )

        # Check file size (read file to get size)
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        max_size = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
            )

    def _extract_pdf_metadata(self, file_path: str) -> dict:
        """Extract metadata from PDF using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            metadata = {
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "mod_date": doc.metadata.get("modDate", ""),
            }
            doc.close()
            return metadata
        except Exception as e:
            return {"error": str(e), "page_count": 0}

    async def upload_pdf(
        self, file: UploadFile, session_id: Optional[str] = None
    ) -> PDFDocument:
        """
        Upload and process PDF file.

        Args:
            file: Uploaded PDF file
            session_id: Optional session identifier to group PDFs

        Returns:
            PDFDocument: Created PDF document record
        """
        # Validate file
        self._validate_pdf(file)

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = file.filename
        safe_filename = f"{timestamp}_{original_filename}"
        file_path = os.path.join(settings.pdf_storage_path, safe_filename)

        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Extract metadata
            pdf_metadata = self._extract_pdf_metadata(file_path)
            page_count = pdf_metadata.get("page_count", 0)

            # Get file size
            file_size = os.path.getsize(file_path)

            # Create database record
            pdf_doc = PDFDocument(
                filename=safe_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                status="uploaded",
                page_count=page_count,
                document_metadata=pdf_metadata,
                session_id=session_id,
                requirements_extracted=False,
                requirements_count=0,
            )

            self.db.add(pdf_doc)
            self.db.commit()
            self.db.refresh(pdf_doc)

            # Update status to 'ready' after successful processing
            pdf_doc.status = "ready"
            self.db.commit()

            return pdf_doc

        except Exception as e:
            # Clean up file if database operation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500, detail=f"Failed to upload PDF: {str(e)}"
            )

    def get_pdf_by_id(self, pdf_id: int) -> Optional[PDFDocument]:
        """Retrieve PDF document by ID."""
        pdf_doc = self.db.query(PDFDocument).filter(PDFDocument.id == pdf_id).first()
        if not pdf_doc:
            raise HTTPException(
                status_code=404, detail=f"PDF with ID {pdf_id} not found"
            )
        return pdf_doc

    def get_all_pdfs(self, skip: int = 0, limit: int = 100) -> list[PDFDocument]:
        """Retrieve all PDF documents with pagination."""
        return self.db.query(PDFDocument).offset(skip).limit(limit).all()

    def get_pdf_count(self) -> int:
        """Get total count of PDF documents."""
        return self.db.query(PDFDocument).count()

    def delete_pdf(self, pdf_id: int) -> bool:
        """
        Delete PDF document and associated file.

        Args:
            pdf_id: ID of PDF to delete

        Returns:
            bool: True if successful
        """
        pdf_doc = self.get_pdf_by_id(pdf_id)

        # Delete physical file
        if os.path.exists(pdf_doc.file_path):
            try:
                os.remove(pdf_doc.file_path)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to delete file: {str(e)}"
                )

        # Delete database record
        self.db.delete(pdf_doc)
        self.db.commit()

        return True

    def get_pdf_file_path(self, pdf_id: int) -> str:
        """Get file path for a PDF document."""
        pdf_doc = self.get_pdf_by_id(pdf_id)
        if not os.path.exists(pdf_doc.file_path):
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        return pdf_doc.file_path
