"""
Agent Service - Extraction Schemas

Pydantic models defining the exact JSON structure the LLM must produce
when extracting structured invoice data from raw text.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ExtractedLineItem(BaseModel):
    """Schema for a single extracted invoice line item."""
    line_number: int = Field(..., description="Sequential line number starting from 1")
    item_code: Optional[str] = Field(None, description="SKU or item code if present")
    description: Optional[str] = Field(None, description="Item description")
    quantity: Optional[Decimal] = Field(None, description="Quantity ordered")
    unit_price: Optional[Decimal] = Field(None, description="Price per unit")
    line_total: Optional[Decimal] = Field(None, description="Total for this line (qty * unit_price)")


class ExtractedInvoice(BaseModel):
    """
    Schema for the full structured invoice extraction.
    
    The LLM must output JSON matching this schema exactly.
    Optional fields are allowed to be null when data is
    missing from the source document.
    """
    invoice_number: Optional[str] = Field(None, description="Invoice number or ID")
    vendor_name: Optional[str] = Field(None, description="Name of the vendor/supplier")
    po_number: Optional[str] = Field(None, description="Purchase Order reference number")
    invoice_date: Optional[str] = Field(None, description="Invoice date in YYYY-MM-DD format")
    currency: Optional[str] = Field(None, description="Currency code (e.g., INR, EUR, USD)")
    total_amount: Optional[Decimal] = Field(None, description="Total invoice amount")
    line_items: list[ExtractedLineItem] = Field(
        default_factory=list,
        description="List of individual line items on the invoice",
    )
