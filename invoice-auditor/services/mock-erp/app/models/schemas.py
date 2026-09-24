"""
Mock ERP - Pydantic Response Schemas

These are the API response models that agent-service will receive
when calling the Mock ERP HTTP endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SKUResponse(BaseModel):
    """Response model for GET /sku/{sku_code}"""
    model_config = ConfigDict(from_attributes=True)

    sku_id: UUID
    sku_code: str
    description: str
    category: str | None
    standard_price: Decimal
    unit_of_measure: str
    active: bool


class VendorResponse(BaseModel):
    """Response model for GET /vendor/{vendor_id}"""
    model_config = ConfigDict(from_attributes=True)

    vendor_id: UUID
    vendor_name: str
    vendor_code: str
    address: str | None
    currency: str
    active: bool


class POLineItemResponse(BaseModel):
    """Line item within a PO response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_number: int
    sku_code: str
    description: str | None
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class PurchaseOrderResponse(BaseModel):
    """Response model for GET /po/{po_number}"""
    model_config = ConfigDict(from_attributes=True)

    po_id: UUID
    po_number: str
    vendor_id: UUID
    po_date: date
    currency: str
    total_amount: Decimal
    status: str
    vendor: VendorResponse
    line_items: list[POLineItemResponse]
