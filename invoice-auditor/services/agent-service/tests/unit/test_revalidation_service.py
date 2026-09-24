import uuid
from unittest.mock import AsyncMock

import pytest

from app.models.database import HumanFeedback, InvoiceAudit
from app.services.revalidation_service import RevalidationService


@pytest.fixture
def mock_invoice_repo():
    return AsyncMock()


@pytest.fixture
def mock_feedback_repo():
    return AsyncMock()


@pytest.fixture
def mock_validation_service():
    return AsyncMock()


@pytest.mark.asyncio
async def test_apply_feedback_and_revalidate(
    mock_invoice_repo, mock_feedback_repo, mock_validation_service
):
    """Test the full flow of overlaying feedback on LLM JSON and revalidating."""
    invoice_id = uuid.uuid4()
    
    # 1. Mock the base LLM output
    mock_invoice = InvoiceAudit(
        invoice_id=invoice_id,
        extracted_raw={
            "total_amount": "150.0",
            "vendor_name": "Wrong Vendor",
        }
    )
    mock_invoice_repo.get_by_id.return_value = mock_invoice
    
    # 2. Mock the historical feedback query to return the correction
    mock_feedback_repo.get_latest_corrections.return_value = {
        "vendor_name": HumanFeedback(
            invoice_id=invoice_id,
            field_name="vendor_name",
            corrected_value="Right Vendor",
            corrected_by="auditor"
        )
    }
    
    # 3. Mock the validation service response
    mock_validation_service.validate_invoice.return_value = {
        "validation_status": "passed",
        "recommendation": "approve",
        "discrepancies": []
    }
    
    service = RevalidationService(
        mock_invoice_repo, mock_feedback_repo, mock_validation_service
    )
    
    corrections = [
        {"field_name": "vendor_name", "corrected_value": "Right Vendor"}
    ]
    
    result = await service.apply_feedback_and_revalidate(
        invoice_id, corrections, "auditor@company.com"
    )
    
    # Assertions
    assert result["recommendation"] == "approve"
    
    # Verify we saved the new feedback
    mock_feedback_repo.create.assert_called_once()
    saved_feedback = mock_feedback_repo.create.call_args[0][0]
    assert saved_feedback.field_name == "vendor_name"
    assert saved_feedback.corrected_value == "Right Vendor"
    
    # Verify the validation service was called with the MERGED data
    called_data = mock_validation_service.validate_invoice.call_args[0][1]
    assert called_data["total_amount"] == "150.0" # From base
    assert called_data["vendor_name"] == "Right Vendor" # From feedback overlay
    
    # Verify we marked feedback as revalidated
    mock_feedback_repo.mark_revalidated.assert_called_once_with(invoice_id)


@pytest.mark.asyncio
async def test_apply_feedback_invoice_not_found(
    mock_invoice_repo, mock_feedback_repo, mock_validation_service
):
    """Test graceful error if the invoice doesn't exist."""
    mock_invoice_repo.get_by_id.return_value = None
    
    service = RevalidationService(
        mock_invoice_repo, mock_feedback_repo, mock_validation_service
    )
    
    result = await service.apply_feedback_and_revalidate(
        uuid.uuid4(), [], "auditor@company.com"
    )
    
    assert "error" in result
    mock_feedback_repo.create.assert_not_called()
