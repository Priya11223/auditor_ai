"""
Human Feedback Repository - CRUD for audit.human_feedback

INSERT-ONLY by design. Original values are never overwritten.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import HumanFeedback


class FeedbackRepository:
    """Repository for audit.human_feedback table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, feedback: HumanFeedback) -> HumanFeedback:
        """
        Insert a human correction record.
        This is INSERT-ONLY — never updates existing records.
        """
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def get_by_invoice_id(
        self, invoice_id: uuid.UUID
    ) -> list[HumanFeedback]:
        """Get all feedback records for an invoice, oldest first."""
        stmt = (
            select(HumanFeedback)
            .where(HumanFeedback.invoice_id == invoice_id)
            .order_by(HumanFeedback.corrected_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_corrections(
        self, invoice_id: uuid.UUID
    ) -> dict[str, HumanFeedback]:
        """
        Get the most recent correction per field for an invoice.
        Returns a dict keyed by field_name.
        Used during revalidation to merge corrections with original values.
        """
        stmt = (
            select(HumanFeedback)
            .where(HumanFeedback.invoice_id == invoice_id)
            .order_by(HumanFeedback.corrected_at.desc())
        )
        result = await self.session.execute(stmt)
        all_feedback = result.scalars().all()

        # Keep only the latest correction per field
        latest: dict[str, HumanFeedback] = {}
        for fb in all_feedback:
            if fb.field_name not in latest:
                latest[fb.field_name] = fb
        return latest

    async def mark_revalidated(
        self, invoice_id: uuid.UUID
    ) -> None:
        """Mark all feedback for an invoice as revalidated."""
        stmt = (
            select(HumanFeedback)
            .where(HumanFeedback.invoice_id == invoice_id)
            .where(HumanFeedback.revalidated == False)  # noqa: E712
        )
        result = await self.session.execute(stmt)
        for fb in result.scalars().all():
            fb.revalidated = True
        await self.session.flush()
