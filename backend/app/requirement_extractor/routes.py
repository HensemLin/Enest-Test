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
    BatchUpdateRequest,
    BatchUpdateResponse,
    ExportRequest,
    ExportResponse,
    ExtractionRequest,
    ExtractionResponse,
    RequirementResponse,
)
from .service import RequirementExtractorService

router = APIRouter(
    prefix="/api/requirements",
    tags=["Requirement Extraction"],
    dependencies=[Depends(verify_api_key_middleware)],
)


def get_requirement_service(
    db: Session = Depends(get_db),
) -> RequirementExtractorService:
    """Dependency to get RequirementExtractorService instance."""
    return RequirementExtractorService(db)


def _extract_requirements_background(pdf_id: int, extraction_mode: str, db: Session):
    """Background task to extract requirements."""
    try:
        service = RequirementExtractorService(db)
        _, requirements = service.extract_requirements(
            pdf_id=pdf_id, extraction_mode=extraction_mode
        )
        print(
            f"✓ Background extraction completed for PDF {pdf_id}: {len(requirements)} requirements extracted"
        )
    except Exception as e:
        print(f"✗ Background extraction failed for PDF {pdf_id}: {e}")

        pdf_service = PDFService(db)
        try:
            pdf_doc = pdf_service.get_pdf_by_id(pdf_id)
            pdf_doc.status = "failed"
            db.commit()
        except:
            pass


@router.post("/extract", response_model=ExtractionResponse)
async def extract_requirements(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    service: RequirementExtractorService = Depends(get_requirement_service),
):
    """
    Extract requirements from a PDF document using LLM (runs in background).

    Args:
        request: Extraction request with pdf_id and mode

    Returns:
        ExtractionResponse with status="processing" (extraction continues in background)
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
        _extract_requirements_background,
        request.pdf_id,
        request.extraction_mode,
        service.db,
    )

    return ExtractionResponse(
        extraction_job_id=extraction_job_id,
        pdf_id=request.pdf_id,
        total_requirements=0,
        status="processing",
        requirements=[],
    )


@router.get("/list", response_model=list[RequirementResponse])
async def list_requirements(
    pdf_id: int = None,
    extraction_job_id: str = None,
    skip: int = 0,
    limit: int = 1000,
    service: RequirementExtractorService = Depends(get_requirement_service),
):
    """
    Get list of requirements with optional filters.

    Args:
        pdf_id: Optional PDF ID filter
        extraction_job_id: Optional extraction job filter
        skip: Number of records to skip
        limit: Maximum number of records

    Returns:
        List of requirements
    """
    requirements = service.get_requirements(
        pdf_id=pdf_id, extraction_job_id=extraction_job_id, skip=skip, limit=limit
    )
    return [RequirementResponse.model_validate(req) for req in requirements]


@router.patch("/batch", response_model=BatchUpdateResponse)
async def batch_update_compliance(
    request: BatchUpdateRequest,
    service: RequirementExtractorService = Depends(get_requirement_service),
):
    """
    Batch update compliance status for multiple requirements.

    Args:
        request: Batch update request with list of updates

    Returns:
        BatchUpdateResponse with count of updated records
    """
    updated_count = service.batch_update_compliance(request.updates)
    return BatchUpdateResponse(
        updated_count=updated_count,
        message=f"Successfully updated {updated_count} requirements"
    )


@router.post("/export", response_model=ExportResponse)
async def export_requirements(
    request: ExportRequest,
    service: RequirementExtractorService = Depends(get_requirement_service),
):
    """
    Export requirements to Excel or JSON file.

    Args:
        request: Export request with format and filters

    Returns:
        ExportResponse with file details
    """
    try:
        if request.format.lower() == "excel":
            file_path, file_name = service.export_to_excel(
                pdf_id=request.pdf_id, extraction_job_id=request.extraction_job_id
            )
        elif request.format.lower() == "json":
            file_path, file_name = service.export_to_json(
                pdf_id=request.pdf_id, extraction_job_id=request.extraction_job_id
            )
        else:
            raise HTTPException(
                status_code=400, detail="Invalid format. Use 'excel' or 'json'"
            )

        requirements = service.get_requirements(
            pdf_id=request.pdf_id, extraction_job_id=request.extraction_job_id
        )

        return ExportResponse(
            file_path=file_path,
            file_name=file_name,
            total_requirements=len(requirements),
            format=request.format,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to export requirements: {str(e)}"
        )


@router.get("/download/{file_name}")
async def download_export(file_name: str):
    """
    Download an exported requirements file.

    Args:
        file_name: Name of the file to download

    Returns:
        File response
    """

    file_path = os.path.join(settings.export_storage_path, file_name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    media_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if file_name.endswith(".xlsx")
        else "application/json"
    )

    return FileResponse(path=file_path, filename=file_name, media_type=media_type)
