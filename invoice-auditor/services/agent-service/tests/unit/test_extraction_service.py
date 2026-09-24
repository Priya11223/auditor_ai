import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services.extraction_service import ExtractionService


@pytest.mark.asyncio
@patch("app.services.extraction_service.pdfplumber")
async def test_extract_pdf_success(mock_pdfplumber):
    """Test successful PDF extraction."""
    # Setup mock
    mock_page = AsyncMock()
    mock_page.extract_text.return_value = "Mock PDF Text"
    
    mock_pdf = AsyncMock()
    mock_pdf.pages = [mock_page]
    mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

    mock_repo = AsyncMock()
    service = ExtractionService(invoice_repo=mock_repo)

    invoice_id = uuid.uuid4()
    result = await service.extract_text("/fake/path.pdf", "pdf", invoice_id)

    assert result["raw_text"] == "Mock PDF Text"
    assert result["extraction_method"] == "pdfplumber"
    assert result["error"] is None

    mock_repo.update_extraction.assert_called_once_with(
        invoice_id=invoice_id,
        raw_text="Mock PDF Text",
        extraction_method="pdfplumber",
    )


@pytest.mark.asyncio
@patch("app.services.extraction_service.docx2txt")
async def test_extract_docx_success(mock_docx2txt):
    """Test successful DOCX extraction."""
    mock_docx2txt.process.return_value = "Mock DOCX Text "
    
    mock_repo = AsyncMock()
    service = ExtractionService(invoice_repo=mock_repo)

    invoice_id = uuid.uuid4()
    result = await service.extract_text("/fake/path.docx", "docx", invoice_id)

    assert result["raw_text"] == "Mock DOCX Text"
    assert result["extraction_method"] == "docx2txt"
    assert result["error"] is None

    mock_repo.update_extraction.assert_called_once_with(
        invoice_id=invoice_id,
        raw_text="Mock DOCX Text",
        extraction_method="docx2txt",
    )


@pytest.mark.asyncio
async def test_extract_unsupported():
    """Test routing failure for unsupported extensions."""
    mock_repo = AsyncMock()
    service = ExtractionService(invoice_repo=mock_repo)

    invoice_id = uuid.uuid4()
    result = await service.extract_text("/fake/path.txt", "txt", invoice_id)

    assert result["raw_text"] == ""
    assert result["extraction_method"] == ""
    assert "Unsupported file type: txt" in result["error"]

    # Should still update DB with failure
    mock_repo.update_extraction.assert_called_once_with(
        invoice_id=invoice_id,
        raw_text="",
        extraction_method="unknown",
    )
