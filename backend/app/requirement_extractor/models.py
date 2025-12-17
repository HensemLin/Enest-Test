import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class ComplianceStatusEnum(str, enum.Enum):
    """Enum for compliance status options."""

    YES = "Yes"
    NO = "No"
    PARTIAL = "Partial"
    UNKNOWN = "Unknown"


class Requirement(Base):
    """Model for extracted tender requirements."""

    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id", ondelete="CASCADE"), index=True)
    extraction_job_id = Column(String(255))
    document_source = Column(String(500))
    category = Column(String(100))
    requirement_detail = Column(Text)
    mandatory_optional = Column(String(50))
    compliance_status = Column(Enum(ComplianceStatusEnum), nullable=True)
    page_number = Column(Integer)
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
