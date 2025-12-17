from sqlalchemy import (
    DECIMAL,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from ..database import Base


class BomItem(Base):
    """Model for Bill of Materials/Quantities items."""

    __tablename__ = "bom_items"

    id = Column(Integer, primary_key=True, nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id", ondelete="CASCADE"), index=True)
    extraction_job_id = Column(String(255))
    item_number = Column(String(100))
    description = Column(Text)
    unit = Column(String(50))
    quantity = Column(DECIMAL(15, 2))
    notes = Column(Text)
    hierarchy_level = Column(Integer)
    parent_item_id = Column(Integer, ForeignKey("bom_items.id", ondelete="CASCADE"))
    is_ambiguous = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
