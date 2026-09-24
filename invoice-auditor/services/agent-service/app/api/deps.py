"""
Agent Service - Dependency Injection

Provides FastAPI dependency functions for injecting
database sessions and repository instances.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db_session
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.line_item_repository import LineItemRepository
from app.repositories.discrepancy_repository import DiscrepancyRepository
from app.repositories.feedback_repository import FeedbackRepository


async def get_invoice_repo(
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceRepository:
    """Inject InvoiceRepository with an active session."""
    return InvoiceRepository(session)


async def get_line_item_repo(
    session: AsyncSession = Depends(get_db_session),
) -> LineItemRepository:
    """Inject LineItemRepository with an active session."""
    return LineItemRepository(session)


async def get_discrepancy_repo(
    session: AsyncSession = Depends(get_db_session),
) -> DiscrepancyRepository:
    """Inject DiscrepancyRepository with an active session."""
    return DiscrepancyRepository(session)


async def get_feedback_repo(
    session: AsyncSession = Depends(get_db_session),
) -> FeedbackRepository:
    """Inject FeedbackRepository with an active session."""
    return FeedbackRepository(session)
