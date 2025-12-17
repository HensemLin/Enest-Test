from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PDFUploadResponse(BaseModel):
    """Response schema for PDF upload."""

    id: int
    filename: str
    original_filename: str
    file_size: int
    status: str
    page_count: Optional[int] = None
    upload_date: datetime
    session_id: Optional[str] = None
    requirements_extracted: bool = False
    requirements_count: int = 0
    last_extraction_date: Optional[datetime] = None
    message: str = "PDF uploaded successfully"

    class Config:
        from_attributes = True


class PDFDocumentResponse(BaseModel):
    """Response schema for PDF document details."""

    id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    upload_date: datetime
    status: str
    page_count: Optional[int] = None
    document_metadata: Optional[dict] = None
    session_id: Optional[str] = None
    requirements_extracted: bool = False
    requirements_count: int = 0
    last_extraction_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class PDFListResponse(BaseModel):
    """Response schema for list of PDFs."""

    total: int
    documents: list[PDFDocumentResponse]


class PDFDeleteResponse(BaseModel):
    """Response schema for PDF deletion."""

    message: str
    deleted_id: int
