import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.models.extraction_schemas import ExtractedInvoice
from app.services.llm_extraction_service import LLMExtractionService


@pytest.fixture
def mock_invoice_repo():
    return AsyncMock()


@pytest.fixture
def mock_line_item_repo():
    return AsyncMock()


@pytest.fixture
def mock_bedrock():
    return AsyncMock()


@pytest.mark.asyncio
@patch("app.services.llm_extraction_service.get_bedrock_client")
async def test_successful_extraction(
    mock_get_bedrock, mock_invoice_repo, mock_line_item_repo, mock_bedrock
):
    """Test successful LLM extraction and database insertion."""
    valid_json = {
        "invoice_number": "INV-100",
        "vendor_name": "Test Vendor",
        "po_number": "PO-123",
        "invoice_date": "2026-09-01",
        "currency": "USD",
        "total_amount": 150.0,
        "line_items": [
            {
                "line_number": 1,
                "item_code": "SKU-1",
                "description": "Widget",
                "quantity": 10,
                "unit_price": 15.0,
                "line_total": 150.0
            }
        ]
    }
    
    mock_bedrock.extract_json.return_value = valid_json
    mock_get_bedrock.return_value = mock_bedrock

    service = LLMExtractionService(
        invoice_repo=mock_invoice_repo, 
        line_item_repo=mock_line_item_repo
    )
    
    invoice_id = uuid.uuid4()
    result = await service.extract_structured_data("Some text", invoice_id)

    assert result["error"] is None
    assert result["parsed_data"]["invoice_number"] == "INV-100"
    
    # Check DB updates
    mock_invoice_repo.update_parsed_fields.assert_called_once()
    mock_line_item_repo.delete_by_invoice_id.assert_called_once_with(invoice_id)
    mock_line_item_repo.create_many.assert_called_once()
    
    # Verify the line item passed to create_many
    created_items = mock_line_item_repo.create_many.call_args[0][0]
    assert len(created_items) == 1
    assert created_items[0].description == "Widget"


@pytest.mark.asyncio
@patch("app.services.llm_extraction_service.get_bedrock_client")
async def test_validation_error(
    mock_get_bedrock, mock_invoice_repo, mock_line_item_repo, mock_bedrock
):
    """Test handling of invalid schema returned by LLM."""
    invalid_json = {
        # Missing line_number in line items
        "line_items": [
            {
                "description": "Widget",
            }
        ]
    }
    
    mock_bedrock.extract_json.return_value = invalid_json
    mock_get_bedrock.return_value = mock_bedrock

    service = LLMExtractionService(
        invoice_repo=mock_invoice_repo, 
        line_item_repo=mock_line_item_repo
    )
    
    invoice_id = uuid.uuid4()
    result = await service.extract_structured_data("Some text", invoice_id)

    assert result["parsed_data"] is None
    assert "LLM returned invalid data schema" in result["error"]
    
    # Should update main DB record with raw JSON but null out parsed fields
    mock_invoice_repo.update_parsed_fields.assert_called_once()
    kwargs = mock_invoice_repo.update_parsed_fields.call_args[1]
    assert kwargs["invoice_number"] is None
    assert kwargs["extracted_raw"] == invalid_json
    
    # Should not attempt to create line items
    mock_line_item_repo.create_many.assert_not_called()
