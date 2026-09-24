"""
Vendor Repository - Read operations for erp.vendors
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Vendor


class VendorRepository:
    """Repository for erp.vendors table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, vendor_id: uuid.UUID) -> Vendor | None:
        """Fetch a vendor by UUID."""
        stmt = select(Vendor).where(Vendor.vendor_id == vendor_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, vendor_code: str) -> Vendor | None:
        """Fetch a vendor by vendor code."""
        stmt = select(Vendor).where(Vendor.vendor_code == vendor_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, vendor_name: str) -> Vendor | None:
        """Fetch a vendor by name (case-insensitive)."""
        stmt = select(Vendor).where(
            Vendor.vendor_name.ilike(vendor_name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
