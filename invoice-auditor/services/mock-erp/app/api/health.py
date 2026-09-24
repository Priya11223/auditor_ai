"""
Mock ERP Service - Health Check Endpoint

Verifies PostgreSQL connectivity (erp schema).
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

# Database URL is injected via environment variable
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/invoice_auditor",
)


async def _check_postgres() -> dict:
    """Verify PostgreSQL connectivity and erp schema existence."""
    try:
        engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()

            # Verify erp schema exists
            schema_result = await conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = 'erp'"
                )
            )
            schemas = [row[0] for row in schema_result.fetchall()]

        await engine.dispose()
        return {
            "status": "healthy",
            "schemas_found": schemas,
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health_check():
    """Liveness probe."""
    return {
        "service": "mock-erp",
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks PostgreSQL connectivity."""
    postgres = await _check_postgres()

    return {
        "service": "mock-erp",
        "status": "ready" if postgres["status"] == "healthy" else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "postgres": postgres,
        },
    }
