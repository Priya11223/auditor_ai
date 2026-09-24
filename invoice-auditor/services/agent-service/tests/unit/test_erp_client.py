import uuid
from unittest.mock import patch

import httpx
import pytest
import respx

from app.clients.erp_client import ERPClient
from app.config.settings import settings


@pytest.fixture
def mock_http_client():
    """Provides a dedicated httpx client for the test rather than the global singleton."""
    return httpx.AsyncClient()


@pytest.mark.asyncio
@respx.mock
@patch("app.clients.erp_client.get_http_client")
async def test_get_po_success(mock_get_client, mock_http_client):
    """Test successful PO fetch."""
    mock_get_client.return_value = mock_http_client
    client = ERPClient()

    vendor_id = str(uuid.uuid4())
    po_id = str(uuid.uuid4())
    
    # Mock the ERP response
    mock_response = {
        "po_id": po_id,
        "po_number": "PO-100",
        "vendor_id": vendor_id,
        "po_date": "2026-09-01",
        "currency": "USD",
        "total_amount": "100.00",
        "status": "open",
        "vendor": {
            "vendor_id": vendor_id,
            "vendor_name": "Test Vendor",
            "vendor_code": "V-1",
            "currency": "USD",
            "active": True
        },
        "line_items": []
    }
    
    url = f"{settings.erp_base_url.rstrip('/')}/po/PO-100"
    respx.get(url).respond(status_code=200, json=mock_response)

    result = await client.get_po("PO-100")
    
    assert result is not None
    assert result.po_number == "PO-100"
    assert str(result.po_id) == po_id
    assert result.vendor.vendor_name == "Test Vendor"


@pytest.mark.asyncio
@respx.mock
@patch("app.clients.erp_client.get_http_client")
async def test_get_po_not_found(mock_get_client, mock_http_client):
    """Test that a 404 cleanly returns None."""
    mock_get_client.return_value = mock_http_client
    client = ERPClient()

    url = f"{settings.erp_base_url.rstrip('/')}/po/INVALID-PO"
    respx.get(url).respond(status_code=404)

    result = await client.get_po("INVALID-PO")
    
    assert result is None


@pytest.mark.asyncio
@respx.mock
@patch("app.clients.erp_client.get_http_client")
async def test_get_po_server_error(mock_get_client, mock_http_client):
    """Test that a 500 raises an HTTPStatusError."""
    mock_get_client.return_value = mock_http_client
    client = ERPClient()

    url = f"{settings.erp_base_url.rstrip('/')}/po/PO-500"
    respx.get(url).respond(status_code=500)

    with pytest.raises(httpx.HTTPStatusError):
        await client.get_po("PO-500")
