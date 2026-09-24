"""
Mock ERP Service - API Routes

Endpoints for fetching PO, Vendor, and SKU data.
Simulates a real ERP system responding with JSON data.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path

from app.api.deps import get_po_repo, get_sku_repo, get_vendor_repo
from app.models.schemas import PurchaseOrderResponse, SKUResponse, VendorResponse
from app.repositories.po_repository import PORepository
from app.repositories.sku_repository import SKURepository
from app.repositories.vendor_repository import VendorRepository

router = APIRouter(tags=["erp"])


@router.get("/po/{po_number}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_number: str = Path(..., description="The Purchase Order number to fetch"),
    po_repo: PORepository = Depends(get_po_repo),
):
    """
    Fetch a Purchase Order by its PO number.
    Returns the PO header, vendor details, and all line items.
    """
    po = await po_repo.get_by_po_number(po_number)
    if not po:
        raise HTTPException(
            status_code=404, detail=f"Purchase Order {po_number} not found"
        )
    return po


@router.get("/vendor/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: uuid.UUID = Path(..., description="The Vendor UUID to fetch"),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
):
    """
    Fetch Vendor details by their UUID.
    """
    vendor = await vendor_repo.get_by_id(vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=404, detail=f"Vendor {vendor_id} not found"
        )
    return vendor


@router.get("/sku/{sku_code}", response_model=SKUResponse)
async def get_sku(
    sku_code: str = Path(..., description="The SKU code to fetch"),
    sku_repo: SKURepository = Depends(get_sku_repo),
):
    """
    Fetch SKU details by its SKU code.
    """
    sku = await sku_repo.get_by_code(sku_code)
    if not sku:
        raise HTTPException(
            status_code=404, detail=f"SKU {sku_code} not found"
        )
    return sku
