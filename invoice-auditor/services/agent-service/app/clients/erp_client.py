"""
Agent Service - Mock ERP HTTP Client

Fetches master data from the Mock ERP API using the centralized httpx client.
"""

import logging
from typing import Optional
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.clients.http_client import get_http_client
from app.config.settings import settings
from app.models.erp_schemas import PurchaseOrderResponse, SKUResponse, VendorResponse

logger = logging.getLogger(__name__)


class ERPClient:
    """Client for communicating with the Mock ERP API."""

    def __init__(self):
        self.base_url = settings.erp_base_url.rstrip("/")

    def _client(self) -> httpx.AsyncClient:
        return get_http_client()

    async def get_po(self, po_number: str) -> Optional[PurchaseOrderResponse]:
        """Fetch a Purchase Order by PO number."""
        url = f"{self.base_url}/po/{po_number}"
        try:
            response = await self._client().get(url)
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            return PurchaseOrderResponse.model_validate(data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching PO {po_number}: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error fetching PO {po_number}: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Schema validation error for PO {po_number}: {e}")
            raise

    async def get_vendor(self, vendor_id: UUID) -> Optional[VendorResponse]:
        """Fetch Vendor details by UUID."""
        url = f"{self.base_url}/vendor/{vendor_id}"
        try:
            response = await self._client().get(url)
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            return VendorResponse.model_validate(data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Vendor {vendor_id}: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error fetching Vendor {vendor_id}: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Schema validation error for Vendor {vendor_id}: {e}")
            raise

    async def get_sku(self, sku_code: str) -> Optional[SKUResponse]:
        """Fetch SKU details by SKU code."""
        url = f"{self.base_url}/sku/{sku_code}"
        try:
            response = await self._client().get(url)
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            data = response.json()
            return SKUResponse.model_validate(data)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching SKU {sku_code}: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Network error fetching SKU {sku_code}: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Schema validation error for SKU {sku_code}: {e}")
            raise
