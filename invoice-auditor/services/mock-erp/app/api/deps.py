"""
Mock ERP Service - Dependency Injection

Provides FastAPI dependency functions for injecting
database sessions and repository instances.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_db_session
from app.repositories.po_repository import PORepository
from app.repositories.vendor_repository import VendorRepository
from app.repositories.sku_repository import SKURepository


async def get_po_repo(
    session: AsyncSession = Depends(get_db_session),
) -> PORepository:
    """Inject PORepository with an active session."""
    return PORepository(session)


async def get_vendor_repo(
    session: AsyncSession = Depends(get_db_session),
) -> VendorRepository:
    """Inject VendorRepository with an active session."""
    return VendorRepository(session)


async def get_sku_repo(
    session: AsyncSession = Depends(get_db_session),
) -> SKURepository:
    """Inject SKURepository with an active session."""
    return SKURepository(session)
