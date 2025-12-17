import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..common.middleware import verify_api_key_middleware
from ..config import settings
from ..database import get_db
from ..pdf_processing.service import PDFService
from .schemas import (
    BomExportRequest,
    BomExportResponse,
    BomExtractionRequest,
    BomExtractionResponse,
    BomItemResponse,
)
from .service import BomExtractorService

router = APIRouter(
    prefix="/api/bom",
    tags=["BoM Extraction"],
    dependencies=[Depends(verify_api_key_middleware)],
)


def get_bom_service(db: Session = Depends(get_db)) -> BomExtractorService:
    """Dependency to get BomExtractorService instance."""
    return BomExtractorService(db)


def _extract_bom_background(pdf_id: int, extraction_mode: str, db: Session):
    """Background task to extract BoM."""
    try:
        service = BomExtractorService(db)
        _, items = service.extract_bom_items(
            pdf_id=pdf_id, extraction_mode=extraction_mode
        )
        print(
            f"✓ Background BoM extraction completed for PDF {pdf_id}: {len(items)} items extracted"
        )
    except Exception as e:
        print(f"✗ Background BoM extraction failed for PDF {pdf_id}: {e}")
        pdf_service = PDFService(db)
        try:
            pdf_doc = pdf_service.get_pdf_by_id(pdf_id)
            pdf_doc.status = "failed"
            db.commit()
        except:
            pass


@router.post("/extract", response_model=BomExtractionResponse)
async def extract_bom(
    request: BomExtractionRequest,
    background_tasks: BackgroundTasks,
    service: BomExtractorService = Depends(get_bom_service),
):
    """
    Extract Bill of Materials from a PDF document (runs in background).

    Args:
        request: Extraction request with pdf_id and mode

    Returns:
        BomExtractionResponse with status="processing" (extraction continues in background)
    """
    extraction_job_id = str(uuid.uuid4())

    pdf_service = PDFService(service.db)

    try:
        pdf_doc = pdf_service.get_pdf_by_id(request.pdf_id)
        pdf_doc.status = "processing"
        service.db.commit()
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"PDF not found: {e}")

    background_tasks.add_task(
        _extract_bom_background, request.pdf_id, request.extraction_mode, service.db
    )

    return BomExtractionResponse(
        extraction_job_id=extraction_job_id,
        pdf_id=request.pdf_id,
        total_items=0,
        status="processing",
        items=[],
    )


@router.get("/list", response_model=list[BomItemResponse])
async def list_bom_items(
    pdf_id: int = None,
    extraction_job_id: str = None,
    skip: int = 0,
    limit: int = 1000,
    service: BomExtractorService = Depends(get_bom_service),
):
    """
    Get list of BoM items with optional filters.

    Args:
        pdf_id: Optional PDF ID filter
        extraction_job_id: Optional extraction job filter
        skip: Number of records to skip
        limit: Maximum number of records

    Returns:
        List of BoM items
    """
    items = service.get_bom_items(
        pdf_id=pdf_id, extraction_job_id=extraction_job_id, skip=skip, limit=limit
    )
    return [BomItemResponse.model_validate(item) for item in items]


@router.post("/export", response_model=BomExportResponse)
async def export_bom(
    request: BomExportRequest, service: BomExtractorService = Depends(get_bom_service)
):
    """
    Export BoM items to Excel file with hierarchy formatting.

    Args:
        request: Export request with filters and formatting options

    Returns:
        BomExportResponse with file details
    """
    try:
        file_path, file_name = service.export_to_excel(
            pdf_id=request.pdf_id,
            extraction_job_id=request.extraction_job_id,
            include_hierarchy=request.include_hierarchy,
        )

        items = service.get_bom_items(
            pdf_id=request.pdf_id, extraction_job_id=request.extraction_job_id
        )

        return BomExportResponse(
            file_path=file_path, file_name=file_name, total_items=len(items)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export BoM: {str(e)}")


@router.get("/download/{file_name}")
async def download_bom_export(file_name: str):
    """
    Download an exported BoM file.

    Args:
        file_name: Name of the file to download

    Returns:
        File response
    """
    file_path = os.path.join(settings.export_storage_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
