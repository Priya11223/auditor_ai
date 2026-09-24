"""
Discrepancy Repository - CRUD for audit.discrepancies
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Discrepancy


class DiscrepancyRepository:
    """Repository for audit.discrepancies table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, discrepancy: Discrepancy) -> Discrepancy:
        """Insert a single discrepancy record."""
        self.session.add(discrepancy)
        await self.session.flush()
        return discrepancy

    async def create_many(
        self, discrepancies: list[Discrepancy]
    ) -> list[Discrepancy]:
        """Insert multiple discrepancy records in batch."""
        self.session.add_all(discrepancies)
        await self.session.flush()
        return discrepancies

    async def get_by_invoice_id(
        self, invoice_id: uuid.UUID
    ) -> list[Discrepancy]:
        """Get all discrepancies for an invoice."""
        stmt = (
            select(Discrepancy)
            .where(Discrepancy.invoice_id == invoice_id)
            .order_by(Discrepancy.detected_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_invoice_id(self, invoice_id: uuid.UUID) -> int:
        """
        Delete all discrepancies for an invoice.
        Used before revalidation to clear stale discrepancies.
        Returns the number of deleted rows.
        """
        stmt = delete(Discrepancy).where(
            Discrepancy.invoice_id == invoice_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount
