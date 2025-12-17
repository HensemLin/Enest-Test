import json
from typing import List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config import settings


class RequirementLLMExtractor:
    """
    LLM-powered requirement extractor for tender documents.

    Uses structured prompting to extract requirements with categories,
    mandatory/optional classification, and compliance status.
    """

    def __init__(self, llm_model: str = None):
        """
        Initialize requirement extractor.

        Args:
            llm_model: LLM model to use for extraction
        """
        self.llm_model = llm_model or settings.llm_model

        self.llm = ChatOpenAI(
            model=self.llm_model,
            temperature=settings.llm_temperature,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
        )

    def extract_requirements_from_text(
        self, text: str, page_number: int, document_source: str
    ) -> List[dict]:
        """
        Extract requirements from text using LLM.

        Args:
            text: Text content to extract from
            page_number: Page number of the text
            document_source: Source document name

        Returns:
            List of requirement dictionaries
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(text, page_number)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self.llm.invoke(messages)
            requirements = self._parse_llm_response(
                response.content, page_number, document_source
            )
            return requirements
        except Exception as e:
            print(f"Error extracting requirements: {e}")
            return []

    def _build_system_prompt(self) -> str:
        """Build system prompt for requirement extraction."""
        return """You are an expert tender requirement extraction assistant.

Your task is to extract ALL requirements from tender documents with high accuracy.

Requirements include:
- Technical specifications
- Functional requirements
- Performance criteria
- Compliance requirements
- Vendor qualifications
- Submission requirements
- Project deliverables
- Timeline requirements
- Quality standards
- Safety requirements

For EACH requirement you extract, provide:
1. **Category**: Type of requirement (Technical, Functional, Compliance, Quality, Timeline, etc.)
2. **Requirement Detail**: Clear, concise statement of the requirement
3. **Mandatory/Optional**: Whether the requirement is "Mandatory" or "Optional" (or "Unclear" if not stated)
4. **Confidence**: Your confidence in this extraction (0.0 to 1.0)

Output Format:
Return a JSON array of requirements in this exact format:
[
  {
    "category": "Category name",
    "requirement_detail": "Clear requirement statement",
    "mandatory_optional": "Mandatory|Optional|Unclear",
    "confidence_score": 0.95
  },
  ...
]

Important:
- Be thorough - extract ALL requirements, even if numerous
- Keep requirement details concise but complete
- Use exact quotes when possible
- If a section contains no requirements, return an empty array []
- Return ONLY valid JSON, no explanations or markdown formatting"""

    def _build_user_prompt(self, text: str, page_number: int) -> str:
        """Build user prompt with text to extract from."""
        return f"""Extract all requirements from the following tender document excerpt.

Page Number: {page_number}

Document Text:
{text}

Requirements (JSON array):"""

    def _parse_llm_response(
        self, response_text: str, page_number: int, document_source: str
    ) -> List[dict]:
        """
        Parse LLM response into requirement dictionaries.

        Args:
            response_text: LLM response text
            page_number: Page number
            document_source: Source document

        Returns:
            List of requirement dictionaries
        """
        try:
            # Clean response text (remove markdown if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            requirements = json.loads(cleaned_text)

            if not isinstance(requirements, list):
                return []

            enhanced_requirements = []
            for req in requirements:
                if not isinstance(req, dict):
                    continue

                enhanced_req = {
                    "document_source": document_source,
                    "category": req.get("category", "Uncategorized"),
                    "requirement_detail": req.get("requirement_detail", ""),
                    "mandatory_optional": req.get("mandatory_optional", "Unclear"),
                    "page_number": page_number,
                    "confidence_score": req.get("confidence_score", 0.5),
                }

                if enhanced_req["requirement_detail"].strip():
                    enhanced_requirements.append(enhanced_req)

            return enhanced_requirements

        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM JSON response: {e}")
            print(f"Response was: {response_text[:500]}")
            return []
        except Exception as e:
            print(f"Error processing LLM response: {e}")
            return []

    def batch_extract_from_pages(
        self, pages: List[dict], document_source: str
    ) -> List[dict]:
        """
        Extract requirements from multiple pages.

        Args:
            pages: List of page dictionaries with 'page_number' and 'text' keys
            document_source: Source document name

        Returns:
            List of all extracted requirements
        """
        all_requirements = []

        for page in pages:
            page_number = page.get("page_number", 0)
            text = page.get("text", "")

            if not text.strip():
                continue

            requirements = self.extract_requirements_from_text(
                text, page_number, document_source
            )
            all_requirements.extend(requirements)

        return all_requirements

    def extract_with_chunking(
        self,
        long_text: str,
        page_number: int,
        document_source: str,
        chunk_size: int = 3000,
    ) -> List[dict]:
        """
        Extract requirements from long text by chunking.

        Args:
            long_text: Long text to extract from
            page_number: Page number
            document_source: Source document
            chunk_size: Maximum characters per chunk

        Returns:
            List of extracted requirements
        """
        chunks = []
        words = long_text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1
            if current_length + word_length > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        all_requirements = []
        for chunk in chunks:
            requirements = self.extract_requirements_from_text(
                chunk, page_number, document_source
            )
            all_requirements.extend(requirements)

        return all_requirements
