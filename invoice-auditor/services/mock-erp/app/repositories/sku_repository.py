"""
SKU Repository - Read operations for erp.sku_master
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import SKUMaster


class SKURepository:
    """Repository for erp.sku_master table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_code(self, sku_code: str) -> SKUMaster | None:
        """Fetch a SKU by its code."""
        stmt = select(SKUMaster).where(SKUMaster.sku_code == sku_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
