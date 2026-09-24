"""
Line Item Repository - CRUD for audit.invoice_line_items
"""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import InvoiceLineItem


class LineItemRepository:
    """Repository for audit.invoice_line_items table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
        """Insert a single line item."""
        self.session.add(line_item)
        await self.session.flush()
        return line_item

    async def create_many(
        self, line_items: list[InvoiceLineItem]
    ) -> list[InvoiceLineItem]:
        """Insert multiple line items in batch."""
        self.session.add_all(line_items)
        await self.session.flush()
        return line_items

    async def get_by_invoice_id(
        self, invoice_id: uuid.UUID
    ) -> list[InvoiceLineItem]:
        """Get all line items for an invoice, ordered by line number."""
        stmt = (
            select(InvoiceLineItem)
            .where(InvoiceLineItem.invoice_id == invoice_id)
            .order_by(InvoiceLineItem.line_number)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_invoice_id(self, invoice_id: uuid.UUID) -> int:
        """
        Delete all line items for an invoice.
        Used before re-parsing to avoid stale rows.
        Returns the number of deleted rows.
        """
        stmt = delete(InvoiceLineItem).where(
            InvoiceLineItem.invoice_id == invoice_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount
