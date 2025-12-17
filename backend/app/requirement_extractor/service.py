import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from ..config import settings
from ..pdf_processing.service import PDFService
from ..pdf_processing.text_extractor import PDFTextExtractor
from .llm_extractor import RequirementLLMExtractor
from .models import Requirement
from .schemas import RequirementCreate, RequirementResponse


class RequirementExtractorService:
    """Service for extracting and managing tender requirements."""

    def __init__(self, db: Session):
        """
        Initialize requirement extractor service.

        Args:
            db: Database session
        """
        self.db = db
        self.pdf_service = PDFService(db)
        self.text_extractor = PDFTextExtractor()
        self.llm_extractor = RequirementLLMExtractor()
        self._ensure_export_dir()

    def _ensure_export_dir(self):
        """Create export directory if it doesn't exist."""
        Path(settings.export_storage_path).mkdir(parents=True, exist_ok=True)

    def extract_requirements(
        self, pdf_id: int, extraction_mode: str = "comprehensive"
    ) -> tuple[str, List[RequirementResponse]]:
        """
        Extract requirements from a PDF document.

        Args:
            pdf_id: PDF document ID
            extraction_mode: 'comprehensive' or 'quick'

        Returns:
            Tuple of (extraction_job_id, list of requirements)
        """
        # Generate unique job ID
        extraction_job_id = str(uuid.uuid4())

        # Get PDF file path and metadata
        pdf_doc = self.pdf_service.get_pdf_by_id(pdf_id)
        pdf_path = pdf_doc.file_path
        document_source = pdf_doc.original_filename

        # Delete old requirements for this PDF (if any)
        old_count = self.delete_requirements(pdf_id=pdf_id)
        if old_count > 0:
            print(f"Deleted {old_count} old requirements for PDF {pdf_id}")

        # Update PDF status to 'processing'
        pdf_doc.status = "processing"
        self.db.commit()

        try:
            # Extract text from PDF (use markdown for better structure)
            pages = self.text_extractor.extract_text_from_pdf(pdf_path, use_markdown=True)

            # Extract requirements using LLM
            if extraction_mode == "quick":
                # Quick mode: Extract from first 10 pages only
                pages = pages[:10]

            all_requirements = self.llm_extractor.batch_extract_from_pages(
                pages, document_source
            )

            # Save requirements to database
            saved_requirements = []
            for req_data in all_requirements:
                requirement = self._save_requirement(pdf_id, extraction_job_id, req_data)
                saved_requirements.append(
                    RequirementResponse.model_validate(requirement)
                )

            # Update PDF document extraction tracking
            pdf_doc.requirements_extracted = True
            pdf_doc.requirements_count = len(saved_requirements)
            pdf_doc.last_extraction_date = datetime.now()
            pdf_doc.status = "ready"
            self.db.commit()

            return extraction_job_id, saved_requirements

        except Exception as e:
            # Update status to 'failed' on error
            pdf_doc.status = "failed"
            self.db.commit()
            raise e

    def _save_requirement(
        self, pdf_id: int, extraction_job_id: str, req_data: dict
    ) -> Requirement:
        """Save a requirement to the database."""
        req_create = RequirementCreate(
            pdf_id=pdf_id,
            extraction_job_id=extraction_job_id,
            document_source=req_data["document_source"],
            category=req_data.get("category"),
            requirement_detail=req_data["requirement_detail"],
            mandatory_optional=req_data.get("mandatory_optional"),
            page_number=req_data.get("page_number"),
            confidence_score=req_data.get("confidence_score"),
        )

        requirement = Requirement(**req_create.model_dump())
        self.db.add(requirement)
        self.db.commit()
        self.db.refresh(requirement)

        return requirement

    def get_requirements(
        self,
        pdf_id: Optional[int] = None,
        extraction_job_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> List[Requirement]:
        """
        Get requirements with optional filters.

        Args:
            pdf_id: Filter by PDF ID
            extraction_job_id: Filter by extraction job
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of Requirement objects
        """
        query = self.db.query(Requirement)

        if pdf_id is not None:
            query = query.filter(Requirement.pdf_id == pdf_id)

        if extraction_job_id is not None:
            query = query.filter(Requirement.extraction_job_id == extraction_job_id)

        return query.offset(skip).limit(limit).all()

    def batch_update_compliance(self, updates: List) -> int:
        """
        Batch update compliance status for multiple requirements.

        Args:
            updates: List of ComplianceUpdate objects with id and compliance_status

        Returns:
            Number of updated requirements
        """
        updated_count = 0

        for update in updates:
            requirement = self.db.query(Requirement).filter(
                Requirement.id == update.id
            ).first()

            if requirement:
                requirement.compliance_status = update.compliance_status
                updated_count += 1

        self.db.commit()
        return updated_count

    def export_to_excel(
        self,
        pdf_id: Optional[int] = None,
        extraction_job_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Export requirements to Excel file.

        Args:
            pdf_id: Optional PDF ID filter
            extraction_job_id: Optional extraction job filter

        Returns:
            Tuple of (file_path, file_name)
        """
        # Get requirements
        requirements = self.get_requirements(
            pdf_id=pdf_id, extraction_job_id=extraction_job_id
        )

        if not requirements:
            raise ValueError("No requirements found to export")

        # Convert to DataFrame
        data = []
        for req in requirements:
            data.append(
                {
                    "ID": req.id,
                    "Document Source": req.document_source,
                    "Category": req.category or "Uncategorized",
                    "Requirement Detail": req.requirement_detail,
                    "Mandatory/Optional": req.mandatory_optional or "Unclear",
                    "Compliance Status": req.compliance_status or "Pending",
                    "Page Number": req.page_number or "N/A",
                    "Confidence Score": req.confidence_score or 0.0,
                    "Extraction Date": req.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        df = pd.DataFrame(data)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if pdf_id:
            file_name = f"requirements_pdf_{pdf_id}_{timestamp}.xlsx"
        elif extraction_job_id:
            file_name = f"requirements_{extraction_job_id[:8]}_{timestamp}.xlsx"
        else:
            file_name = f"requirements_all_{timestamp}.xlsx"

        file_path = os.path.join(settings.export_storage_path, file_name)

        # Write to Excel with formatting
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Requirements", index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets["Requirements"]
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(), len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(
                    max_length + 2, 100
                )

        return file_path, file_name

    def export_to_json(
        self,
        pdf_id: Optional[int] = None,
        extraction_job_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Export requirements to JSON file.

        Args:
            pdf_id: Optional PDF ID filter
            extraction_job_id: Optional extraction job filter

        Returns:
            Tuple of (file_path, file_name)
        """
        # Get requirements
        requirements = self.get_requirements(
            pdf_id=pdf_id, extraction_job_id=extraction_job_id
        )

        if not requirements:
            raise ValueError("No requirements found to export")

        # Convert to list of dicts
        data = []
        for req in requirements:
            data.append(
                {
                    "id": req.id,
                    "pdf_id": req.pdf_id,
                    "extraction_job_id": req.extraction_job_id,
                    "document_source": req.document_source,
                    "category": req.category,
                    "requirement_detail": req.requirement_detail,
                    "mandatory_optional": req.mandatory_optional,
                    "compliance_status": req.compliance_status,
                    "page_number": req.page_number,
                    "confidence_score": req.confidence_score,
                    "created_at": req.created_at.isoformat(),
                }
            )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if pdf_id:
            file_name = f"requirements_pdf_{pdf_id}_{timestamp}.json"
        elif extraction_job_id:
            file_name = f"requirements_{extraction_job_id[:8]}_{timestamp}.json"
        else:
            file_name = f"requirements_all_{timestamp}.json"

        file_path = os.path.join(settings.export_storage_path, file_name)

        # Write to JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {"requirements": data, "total": len(data), "exported_at": timestamp},
                f,
                indent=2,
                ensure_ascii=False,
            )

        return file_path, file_name

    def delete_requirements(
        self, pdf_id: Optional[int] = None, extraction_job_id: Optional[str] = None
    ) -> int:
        """
        Delete requirements with optional filters.

        Args:
            pdf_id: Filter by PDF ID
            extraction_job_id: Filter by extraction job

        Returns:
            Number of requirements deleted
        """
        query = self.db.query(Requirement)

        if pdf_id is not None:
            query = query.filter(Requirement.pdf_id == pdf_id)

        if extraction_job_id is not None:
            query = query.filter(Requirement.extraction_job_id == extraction_job_id)

        count = query.count()
        query.delete()
        self.db.commit()

        return count
