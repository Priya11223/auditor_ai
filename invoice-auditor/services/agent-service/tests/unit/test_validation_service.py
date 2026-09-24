import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.database import Discrepancy
from app.services.validation_service import ValidationService


@pytest.fixture
def mock_invoice_repo():
    return AsyncMock()


@pytest.fixture
def mock_discrepancy_repo():
    return AsyncMock()


@pytest.fixture
def mock_erp_client():
    return AsyncMock()


@pytest.mark.asyncio
@patch("app.services.validation_service.ERPClient")
async def test_validation_all_passed(
    MockERPClient, mock_invoice_repo, mock_discrepancy_repo
):
    """Test a perfectly matching invoice against ERP."""
    mock_erp_instance = AsyncMock()
    MockERPClient.return_value = mock_erp_instance

    # Mock ERP PO
    po_mock = AsyncMock()
    po_mock.total_amount = Decimal("150.0")
    po_mock.vendor.vendor_name = "Test Vendor"
    
    line_mock = AsyncMock()
    line_mock.sku_code = "SKU-1"
    line_mock.quantity = Decimal("10")
    line_mock.unit_price = Decimal("15.0")
    
    po_mock.line_items = [line_mock]
    mock_erp_instance.get_po.return_value = po_mock

    service = ValidationService(mock_invoice_repo, mock_discrepancy_repo)

    parsed_data = {
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
    
    invoice_id = uuid.uuid4()
    result = await service.validate_invoice(invoice_id, parsed_data)

    assert result["validation_status"] == "passed"
    assert result["recommendation"] == "approve"
    assert len(result["discrepancies"]) == 0
    mock_discrepancy_repo.create_many.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.validation_service.ERPClient")
async def test_validation_arithmetic_failure(
    MockERPClient, mock_invoice_repo, mock_discrepancy_repo
):
    """Test invoice math doesn't add up."""
    mock_erp_instance = AsyncMock()
    MockERPClient.return_value = mock_erp_instance
    mock_erp_instance.get_po.return_value = AsyncMock() # Just bypass ERP checks for this test

    service = ValidationService(mock_invoice_repo, mock_discrepancy_repo)

    parsed_data = {
        "invoice_number": "INV-100",
        "vendor_name": "Test Vendor",
        "po_number": "PO-123",
        "invoice_date": "2026-09-01",
        "currency": "USD",
        "total_amount": 200.0, # Math error, should be 150
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
    
    invoice_id = uuid.uuid4()
    result = await service.validate_invoice(invoice_id, parsed_data)

    assert result["validation_status"] == "failed"
    assert result["recommendation"] == "reject"
    assert any(d["field"] == "total_amount_math" for d in result["discrepancies"])


@pytest.mark.asyncio
@patch("app.services.validation_service.ERPClient")
async def test_validation_missing_po(
    MockERPClient, mock_invoice_repo, mock_discrepancy_repo
):
    """Test ERP returns 404 for PO."""
    mock_erp_instance = AsyncMock()
    MockERPClient.return_value = mock_erp_instance
    mock_erp_instance.get_po.return_value = None

    service = ValidationService(mock_invoice_repo, mock_discrepancy_repo)

    parsed_data = {
        "invoice_number": "INV-100",
        "vendor_name": "Test Vendor",
        "po_number": "INVALID-PO",
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
    
    invoice_id = uuid.uuid4()
    result = await service.validate_invoice(invoice_id, parsed_data)

    assert result["validation_status"] == "failed"
    assert result["recommendation"] == "reject"
    assert any(d["field"] == "po_number" for d in result["discrepancies"])
