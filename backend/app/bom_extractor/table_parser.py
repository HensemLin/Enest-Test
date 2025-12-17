"""LLM-based Bill of Materials extractor using pymupdf4llm for markdown conversion."""

import json
from typing import List

import pymupdf4llm
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import settings


class BomTableParser:
    """
    Parse Bill of Materials tables from PDF documents using LLM.

    Uses pymupdf4llm for optimal markdown conversion + few-shot prompting.
    """

    def __init__(self, extraction_mode: str = "auto"):
        """
        Initialize BoM table parser.

        Args:
            extraction_mode: Extraction strategy
                - 'auto': Standard LLM extraction (temperature 0.1)
                - 'strict': Lower temperature, more conservative (0.0)
                - 'fuzzy': Higher temperature, more flexible (0.3)
        """
        self.extraction_mode = extraction_mode

        # Adjust temperature based on mode
        temp_map = {"strict": 0.0, "auto": 0.1, "fuzzy": 0.3}
        temperature = temp_map.get(extraction_mode, 0.1)

        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=temperature,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

    def extract_bom_content_from_pdf(
        self, pdf_path: str, use_full_document: bool = True
    ) -> List[dict]:
        """
        Extract BoM content from PDF as markdown using pymupdf4llm.

        Args:
            pdf_path: Path to PDF file
            use_full_document: If True, extract entire document as one context (better for cross-page content)
                             If False, extract page by page (better for memory)

        Returns:
            List of dictionaries with markdown content
        """
        if use_full_document:
            # Extract entire document as single markdown for better context
            full_markdown = pymupdf4llm.to_markdown(
                pdf_path,
                page_chunks=False,
                write_images=False,
                show_progress=False,
            )

            if isinstance(full_markdown, list):
                full_text = "\n\n".join([p.get("text", "") for p in full_markdown])
            else:
                full_text = full_markdown

            return [
                {
                    "page_number": 1,
                    "markdown": full_text.strip(),
                    "method": "pymupdf4llm_full_document",
                }
            ]
        else:
            # Get document as list of page dictionaries (original behavior)
            pages_data = pymupdf4llm.to_markdown(
                pdf_path,
                page_chunks=True,
                write_images=False,
                show_progress=False,
            )

            all_pages = []
            for page_dict in pages_data:
                markdown_content = page_dict.get("text", "")

                page_number = page_dict.get("metadata", {}).get(
                    "page", len(all_pages) + 1
                )

                if markdown_content.strip():
                    all_pages.append(
                        {
                            "page_number": page_number,
                            "markdown": markdown_content.strip(),
                            "method": "pymupdf4llm",
                        }
                    )
            return all_pages

    def parse_bom_items(
        self, tables: List[dict], pdf_id: int, extraction_job_id: str
    ) -> List[dict]:
        """
        Parse BoM items from extracted markdown using LLM.

        Args:
            tables: List of page dictionaries with markdown content
            pdf_id: PDF document ID
            extraction_job_id: Extraction job ID

        Returns:
            List of BoM item dictionaries
        """
        all_items = []

        for page_data in tables:
            markdown_content = page_data.get("markdown", "")
            page_number = page_data.get("page_number", 1)
            extraction_method = page_data.get("method", "")

            if not markdown_content or len(markdown_content) < 50:
                print(f"Warning: Page {page_number} has no substantial content")
                continue

            # Extract items using LLM
            is_full_document = "full_document" in extraction_method
            page_items = self._extract_with_llm(
                markdown_content, page_number, add_page_info=not is_full_document
            )

            for item in page_items:
                item["pdf_id"] = pdf_id
                item["extraction_job_id"] = extraction_job_id

            all_items.extend(page_items)

        return all_items

    def _build_extraction_prompt(self, markdown_content: str, page_number: int) -> str:
        """
        Build LLM prompt with few-shot example from assignment.

        Args:
            markdown_content: Markdown-formatted page content
            page_number: Page number

        Returns:
            Complete prompt string
        """
        return f"""You are an expert at extracting Bill of Materials (BoM) and Bill of Quantities (BoQ) from tender documents.

# Task
Extract concise Bill of Materials and Bill of Quantities items. Focus on WHAT equipment/materials are being supplied, NOT verbose scope-of-work descriptions.

# Key Principles

1. **BoM = Materials & Equipment** - Extract actual materials, equipment, components with quantities
2. **BoQ = Work Items** - Extract specific work activities (supply, installation, testing, etc.)
3. **Concise Descriptions** - Use short, clear descriptions of the item/work, NOT lengthy scope text
4. **Break Down Complex Items** - If a row lists multiple equipment/materials, extract each as a sub-item

# Critical Instructions

1. **For Items with Multiple Equipment Listed**:
   - If a row lists MULTIPLE equipment/materials with quantities in bullet points
   - Extract EACH piece of equipment as a SEPARATE row
   - Use the SAME item_number for all equipment from that row
   - Each equipment row gets its own unit and quantity

   Example:
   - Row says: "Item 1: Design, engineering, supply... including: • 500 MVA ICT: 2 nos • 400kV bays: 2 nos • 220kV bays: 2 nos"
   - Extract as MULTIPLE rows:
     - item_number="1", description="500 MVA, 400/220kV ICT", unit="Nos", quantity=2, hierarchy_level=1
     - item_number="1", description="400 kV ICT bays", unit="Nos", quantity=2, hierarchy_level=1
     - item_number="1", description="220 kV ICT bays", unit="Nos", quantity=2, hierarchy_level=1

   - Then when you see "Item 1A: Ex works supply..."
   - Extract as:
     - item_number="1A", description="Ex works supply of all equipments", unit="LSTK", quantity=1, hierarchy_level=1

   **KEY POINT**: Multiple rows can have the SAME item_number if they represent different equipment from the same table row.

2. **Item Numbering**:
   - Use EXACT item numbers from the table: 1, 1A, 1B, 2, 2A
   - DO NOT invent numbers like 1.1, 1.2, 1.3
   - If one table row lists 5 pieces of equipment, create 5 rows all with the same item_number

3. **Extract Fields**:
   - `item_number`: EXACT item code from table (1, 1A, 1B, 2, 2A, etc.) - multiple rows can share same number
   - `description`: CONCISE description of the material/equipment/work (max 10-15 words)
   - `unit`: Unit of measurement (Nos, Set, LSTK, m3, kg, etc.)
   - `quantity`: Numerical quantity only
   - `notes`: Additional specs or clarifications
   - `hierarchy_level`: 0=parent, 1=child, 2=grandchild
   - `is_ambiguous`: true if unclear

4. **What to Extract as Separate Items**:
   ✓ Each equipment/material with a quantity (500 MVA ICT: 2 nos)
   ✓ Each distinct work item (Ex works supply, Transportation, Installation)
   ✓ Each service with a unit (LSTK items)

5. **What NOT to Include in Description**:
   ✗ Long scope-of-work text ("Design, engineering, supply, testing at manufacturer's works...")
   ✗ Contractual terms ("including insurance & storage, associated civil works...")
   ✗ Process descriptions ("unloading and delivery at site including...")

   → Put these details in the `notes` field if important

6. **Handle Missing Information**: Set to null if not available, still include the item.

# Few-Shot Example

**Input Markdown:**
```markdown
# BID PRICE SCHEDULE

| Item No. | Description of Work | Unit | Quantity | Rate | Amount |
|----------|-------------------|------|----------|------|--------|
| 1 | Supply, installation of 500 MVA, 400/220kV ICT including ex-works supply, transport, insurance, erection and commissioning | - | - | - | - |
| 1A | Ex works supply of 2 nos. 500 MVA ICT transformers | Nos | 2 | - | - |
| 1B | Transportation and insurance from factory to site | LSTK | 1 | - | - |
| 1C | Civil works for transformer foundation | LSTK | 1 | - | - |
| 2 | 400kV GIS Bay extension works | - | - | - | - |
| 2A | Supply of 400kV SF6 GIS equipment | Set | 2 | - | - |

Note: All prices in INR
```

**Output JSON:**
```json
[
  {{
    "item_number": "1",
    "description": "500 MVA, 400/220kV ICT",
    "unit": "Nos",
    "quantity": 2,
    "notes": "Inter-connecting Transformer",
    "hierarchy_level": 1,
    "is_ambiguous": false
  }},
  {{
    "item_number": "1A",
    "description": "Ex works supply of ICT transformers",
    "unit": "Nos",
    "quantity": 2,
    "notes": "Factory supply",
    "hierarchy_level": 1,
    "is_ambiguous": false
  }},
  {{
    "item_number": "1B",
    "description": "Transportation and insurance from factory to site",
    "unit": "LSTK",
    "quantity": 1,
    "notes": "Lump sum turnkey for transport",
    "hierarchy_level": 1,
    "is_ambiguous": false
  }},
  {{
    "item_number": "1C",
    "description": "Civil works for transformer foundation",
    "unit": "LSTK",
    "quantity": 1,
    "notes": "Foundation construction",
    "hierarchy_level": 1,
    "is_ambiguous": false
  }},
  {{
    "item_number": "2",
    "description": "400kV GIS Bay extension",
    "unit": null,
    "quantity": null,
    "notes": "GIS Bay work package",
    "hierarchy_level": 2,
    "is_ambiguous": false
  }},
  {{
    "item_number": "2A",
    "description": "400kV SF6 GIS equipment",
    "unit": "Set",
    "quantity": 2,
    "notes": "Gas Insulated Switchgear",
    "hierarchy_level": 2,
    "is_ambiguous": false
  }}
]
```

# Actual Page Content to Extract (Page {page_number})

```markdown
{markdown_content}
```

# Output Requirements

- Return ONLY a valid JSON array
- Include ALL items from the page
- Preserve exact hierarchy relationships
- Use null for missing values (never use empty strings)
- Set `is_ambiguous: true` if information is unclear
- Be thorough - extract every line item
- Use page context (headers, notes) to improve accuracy

Output JSON:"""

    def _extract_with_llm(
        self, markdown_content: str, page_number: int, add_page_info: bool = True
    ) -> List[dict]:
        """
        Extract BoM items using LLM with few-shot prompting.

        Args:
            markdown_content: Markdown-formatted page content
            page_number: Page number
            add_page_info: Whether to add page number to notes

        Returns:
            List of BoM item dictionaries
        """
        prompt = self._build_extraction_prompt(markdown_content, page_number)

        messages = [
            SystemMessage(
                content="You are an expert BoM extraction system. Output only valid JSON arrays."
            ),
            HumanMessage(content=prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            response_text = response.content.strip()

            # Remove markdown code block if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            bom_items = json.loads(response_text)

            if not isinstance(bom_items, list):
                print(f"Warning: LLM returned non-list response for page {page_number}")
                return []

            if add_page_info:
                for item in bom_items:
                    page_info = f"Page {page_number}"
                    if item.get("notes"):
                        item["notes"] = f"{item['notes']} | {page_info}"
                    else:
                        item["notes"] = page_info

            return bom_items

        except json.JSONDecodeError as e:
            print(
                f"Error: Failed to parse LLM response as JSON for page {page_number}: {e}"
            )
            print(f"Response was: {response_text[:500]}")
            return []
        except Exception as e:
            print(f"Error extracting BoM from page {page_number}: {e}")
            return []
