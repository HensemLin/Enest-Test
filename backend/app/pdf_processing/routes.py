from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from ..common.middleware import verify_api_key_middleware
from ..database import get_db
from .schemas import (
    PDFDeleteResponse,
    PDFDocumentResponse,
    PDFListResponse,
    PDFUploadResponse,
)
from .service import PDFService

router = APIRouter(
    prefix="/api/pdfs",
    tags=["PDF Management"],
    dependencies=[Depends(verify_api_key_middleware)],
)


def get_pdf_service(db: Session = Depends(get_db)) -> PDFService:
    """Dependency to get PDFService instance."""
    return PDFService(db)


@router.post("/upload", response_model=PDFUploadResponse, status_code=201)
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    service: PDFService = Depends(get_pdf_service),
):
    """
    Upload a PDF document.

    Args:
        file: PDF file to upload (max 100MB)
        session_id: Optional session ID to group related PDFs together

    Returns:
        PDFUploadResponse with document details
    """
    pdf_doc = await service.upload_pdf(file, session_id=session_id)

    return PDFUploadResponse(
        id=pdf_doc.id,
        filename=pdf_doc.filename,
        original_filename=pdf_doc.original_filename,
        file_size=pdf_doc.file_size,
        status=pdf_doc.status,
        page_count=pdf_doc.page_count,
        upload_date=pdf_doc.upload_date,
        session_id=pdf_doc.session_id,
        requirements_extracted=pdf_doc.requirements_extracted,
        requirements_count=pdf_doc.requirements_count,
        last_extraction_date=pdf_doc.last_extraction_date,
    )


@router.get("", response_model=PDFListResponse)
@router.get("/", response_model=PDFListResponse)
async def list_pdfs(
    skip: int = 0, limit: int = 100, service: PDFService = Depends(get_pdf_service)
):
    """
    Get list of all uploaded PDFs.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        PDFListResponse with list of documents
    """
    documents = service.get_all_pdfs(skip=skip, limit=limit)
    total = service.get_pdf_count()

    return PDFListResponse(total=total, documents=documents)


@router.get("/{pdf_id}", response_model=PDFDocumentResponse)
async def get_pdf(pdf_id: int, service: PDFService = Depends(get_pdf_service)):
    """
    Get details of a specific PDF document.

    Args:
        pdf_id: ID of the PDF document

    Returns:
        PDFDocumentResponse with document details
    """
    return service.get_pdf_by_id(pdf_id)


@router.delete("/{pdf_id}", response_model=PDFDeleteResponse)
async def delete_pdf(pdf_id: int, service: PDFService = Depends(get_pdf_service)):
    """
    Delete a PDF document and its associated file.

    Args:
        pdf_id: ID of the PDF document to delete

    Returns:
        PDFDeleteResponse with deletion confirmation
    """
    service.delete_pdf(pdf_id)
    return PDFDeleteResponse(message="PDF deleted successfully", deleted_id=pdf_id)
