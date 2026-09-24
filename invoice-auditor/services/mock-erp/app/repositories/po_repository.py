"""
PO Repository - Read operations for erp.purchase_orders + erp.po_line_items
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import PurchaseOrder


class PORepository:
    """Repository for erp.purchase_orders table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_po_number(self, po_number: str) -> PurchaseOrder | None:
        """
        Fetch a PO by its number.
        Eager-loads line_items and vendor via selectin.
        """
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.po_number == po_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
