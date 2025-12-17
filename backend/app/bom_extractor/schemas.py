from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class BomItemCreate(BaseModel):
    """Schema for creating a BoM item."""

    pdf_id: int
    extraction_job_id: str
    item_number: Optional[str] = None
    description: str
    unit: Optional[str] = None
    quantity: Optional[Decimal] = None
    notes: Optional[str] = None
    hierarchy_level: int = 0
    parent_item_id: Optional[int] = None
    is_ambiguous: bool = False


class BomItemResponse(BaseModel):
    """Schema for BoM item response."""

    id: int
    pdf_id: int
    extraction_job_id: str
    item_number: Optional[str] = None
    description: str
    unit: Optional[str] = None
    quantity: Optional[Decimal] = None
    notes: Optional[str] = None
    hierarchy_level: int
    parent_item_id: Optional[int] = None
    is_ambiguous: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BomExtractionRequest(BaseModel):
    """Schema for BoM extraction request."""

    pdf_id: int
    extraction_mode: str = "auto"


class BomExtractionResponse(BaseModel):
    """Schema for BoM extraction response."""

    extraction_job_id: str
    pdf_id: int
    total_items: int
    status: str
    items: List[BomItemResponse]
    message: str = "BoM items extracted successfully"


class BomExportRequest(BaseModel):
    """Schema for BoM export request."""

    pdf_id: Optional[int] = None
    extraction_job_id: Optional[str] = None
    include_hierarchy: bool = True


class BomExportResponse(BaseModel):
    """Schema for BoM export response."""

    file_path: str
    file_name: str
    total_items: int
    message: str = "BoM export completed successfully"
