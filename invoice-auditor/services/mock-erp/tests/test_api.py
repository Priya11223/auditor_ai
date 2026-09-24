import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_po_repo, get_sku_repo, get_vendor_repo
from app.models.database import PurchaseOrder, SKUMaster, Vendor


def test_get_po_success(client: TestClient):
    """Test successful retrieval of a Purchase Order."""
    # Setup mock
    mock_repo = AsyncMock()
    
    vendor_id = uuid.uuid4()
    po_id = uuid.uuid4()
    
    mock_po = PurchaseOrder(
        po_id=po_id,
        po_number="PO-1001",
        vendor_id=vendor_id,
        po_date="2026-09-01",
        currency="INR",
        total_amount=Decimal("10500.0000"),
        status="open",
        vendor=Vendor(
            vendor_id=vendor_id,
            vendor_name="ABC Corp",
            vendor_code="VENDOR-001",
            address="123 Business Park, Mumbai, India",
            currency="INR",
            active=True,
        ),
        line_items=[],
    )
    mock_repo.get_by_po_number.return_value = mock_po

    # Apply dependency override
    client.app.dependency_overrides[get_po_repo] = lambda: mock_repo

    # Act
    response = client.get("/po/PO-1001")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["po_number"] == "PO-1001"
    assert data["vendor"]["vendor_name"] == "ABC Corp"

    # Cleanup
    client.app.dependency_overrides.clear()


def test_get_po_not_found(client: TestClient):
    """Test 404 response when Purchase Order is not found."""
    mock_repo = AsyncMock()
    mock_repo.get_by_po_number.return_value = None

    client.app.dependency_overrides[get_po_repo] = lambda: mock_repo

    response = client.get("/po/INVALID-PO")

    assert response.status_code == 404
    assert response.json()["detail"] == "Purchase Order INVALID-PO not found"

    client.app.dependency_overrides.clear()


def test_get_vendor_success(client: TestClient):
    """Test successful retrieval of a Vendor."""
    mock_repo = AsyncMock()
    
    vendor_id = uuid.uuid4()
    
    mock_vendor = Vendor(
        vendor_id=vendor_id,
        vendor_name="ABC Corp",
        vendor_code="VENDOR-001",
        address="123 Business Park, Mumbai, India",
        currency="INR",
        active=True,
    )
    mock_repo.get_by_id.return_value = mock_vendor

    client.app.dependency_overrides[get_vendor_repo] = lambda: mock_repo

    response = client.get(f"/vendor/{vendor_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["vendor_name"] == "ABC Corp"

    client.app.dependency_overrides.clear()


def test_get_sku_success(client: TestClient):
    """Test successful retrieval of a SKU."""
    mock_repo = AsyncMock()
    
    sku_id = uuid.uuid4()
    
    mock_sku = SKUMaster(
        sku_id=sku_id,
        sku_code="SKU-001",
        description="Laptop - Business Grade",
        category="Electronics",
        standard_price=Decimal("1000.0000"),
        unit_of_measure="EA",
        active=True,
    )
    mock_repo.get_by_code.return_value = mock_sku

    client.app.dependency_overrides[get_sku_repo] = lambda: mock_repo

    response = client.get("/sku/SKU-001")

    assert response.status_code == 200
    data = response.json()
    assert data["sku_code"] == "SKU-001"
    assert data["description"] == "Laptop - Business Grade"

    client.app.dependency_overrides.clear()
