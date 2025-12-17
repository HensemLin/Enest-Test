from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ..database import Base


class PDFDocument(Base):
    """Model for uploaded PDF documents."""

    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True, nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50))
    page_count = Column(Integer)
    document_metadata = Column(JSONB)

    # Session and extraction tracking
    session_id = Column(String(255), index=True)
    requirements_extracted = Column(Boolean, default=False)
    requirements_count = Column(Integer, default=0)
    last_extraction_date = Column(DateTime(timezone=True))
