"""
Agent Service - ERP API Response Schemas

Pydantic models representing the expected JSON structures
returned by the Mock ERP service.
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SKUResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sku_id: UUID
    sku_code: str
    description: str
    category: Optional[str]
    standard_price: Decimal
    unit_of_measure: str
    active: bool


class VendorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    vendor_id: UUID
    vendor_name: str
    vendor_code: str
    address: Optional[str]
    currency: str
    active: bool


class POLineItemResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    line_number: int
    sku_code: str
    description: Optional[str]
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    po_id: UUID
    po_number: str
    vendor_id: UUID
    po_date: date
    currency: str
    total_amount: Decimal
    status: str
    vendor: VendorResponse
    line_items: list[POLineItemResponse]
