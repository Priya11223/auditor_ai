"""
Mock ERP Service - Database Configuration

Provides async SQLAlchemy engine, session factory, and base model.
All erp schema operations go through this module.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/invoice_auditor",
)

# --- Async Engine ---
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)

# --- Session Factory ---
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Declarative Base ---
class Base(DeclarativeBase):
    """Base class for all Mock ERP ORM models."""
    pass


async def get_db_session() -> AsyncSession:
    """Dependency-injectable async session generator."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
