"""
Agent Service - Extraction Service

Routes document paths to the appropriate extraction engine
based on file extension and updates the database.
"""

import logging
import uuid
from pathlib import Path

import docx2txt
import pdfplumber
import pytesseract
from PIL import Image

from app.repositories.invoice_repository import InvoiceRepository

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting raw text from supported file types."""

    def __init__(self, invoice_repo: InvoiceRepository):
        self.invoice_repo = invoice_repo

    async def extract_text(self, file_path: str, file_type: str, invoice_id: uuid.UUID) -> dict:
        """
        Extract text and update the invoice record.
        Returns a state dictionary for the LangGraph workflow.
        """
        raw_text = ""
        error_msg = None
        method = ""

        try:
            if file_type == "pdf":
                raw_text = self._extract_pdf(file_path)
                method = "pdfplumber"
            elif file_type == "docx":
                raw_text = self._extract_docx(file_path)
                method = "docx2txt"
            elif file_type == "png":
                raw_text = self._extract_png(file_path)
                method = "pytesseract"
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Update DB with successful extraction
            await self.invoice_repo.update_extraction(
                invoice_id=invoice_id,
                raw_text=raw_text,
                extraction_method=method,
            )
            logger.info(f"Successfully extracted {len(raw_text)} chars from {file_path} via {method}")

        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            logger.error(f"Error extracting {file_path}: {e}")
            # Still update the DB to record the failure method attempt
            await self.invoice_repo.update_extraction(
                invoice_id=invoice_id,
                raw_text="",
                extraction_method=method if method else "unknown",
            )

        return {
            "raw_text": raw_text,
            "extraction_method": method,
            "error": error_msg,
        }

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        text_pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
        return "\n\n".join(text_pages).strip()

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX using docx2txt."""
        return docx2txt.process(file_path).strip()

    def _extract_png(self, file_path: str) -> str:
        """Extract text from PNG using pytesseract."""
        image = Image.open(file_path)
        return pytesseract.image_to_string(image).strip()
