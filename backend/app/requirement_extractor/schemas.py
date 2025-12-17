from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel

# Compliance status options
ComplianceStatus = Literal["Yes", "No", "Partial", "Unknown"]


class RequirementCreate(BaseModel):
    """Schema for creating a requirement."""

    pdf_id: int
    extraction_job_id: str
    document_source: str
    category: Optional[str] = None
    requirement_detail: str
    mandatory_optional: Optional[str] = None
    compliance_status: Optional[ComplianceStatus] = None  # Must be one of: Yes/No/Partial/Unknown
    page_number: Optional[int] = None
    confidence_score: Optional[float] = None


class RequirementResponse(BaseModel):
    """Schema for requirement response."""

    id: int
    pdf_id: int
    extraction_job_id: str
    document_source: str
    category: Optional[str] = None
    requirement_detail: str
    mandatory_optional: Optional[str] = None
    compliance_status: Optional[ComplianceStatus] = None  # Must be one of: Yes/No/Partial/Unknown
    page_number: Optional[int] = None
    confidence_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractionRequest(BaseModel):
    """Schema for requirement extraction request."""

    pdf_id: int
    extraction_mode: str = "comprehensive"  # 'comprehensive' or 'quick'


class ExtractionResponse(BaseModel):
    """Schema for extraction response."""

    extraction_job_id: str
    pdf_id: int
    total_requirements: int
    status: str  # 'completed', 'in_progress', 'failed'
    requirements: List[RequirementResponse]
    message: str = "Requirements extracted successfully"


class ExportRequest(BaseModel):
    """Schema for export request."""

    pdf_id: Optional[int] = None  # If None, export all
    extraction_job_id: Optional[str] = None  # Filter by specific extraction job
    format: str = "excel"  # 'excel' or 'json'


class ExportResponse(BaseModel):
    """Schema for export response."""

    file_path: str
    file_name: str
    total_requirements: int
    format: str
    message: str = "Export completed successfully"


class ComplianceUpdate(BaseModel):
    """Schema for single compliance status update."""

    id: int
    compliance_status: ComplianceStatus


class BatchUpdateRequest(BaseModel):
    """Schema for batch compliance status updates."""

    updates: List[ComplianceUpdate]


class BatchUpdateResponse(BaseModel):
    """Schema for batch update response."""

    updated_count: int
    message: str = "Compliance statuses updated successfully"
