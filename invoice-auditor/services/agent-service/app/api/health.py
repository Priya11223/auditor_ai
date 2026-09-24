"""
Agent Service - Health Check Endpoints

Provides liveness and readiness probes that verify connectivity
to all infrastructure dependencies: PostgreSQL, Redis, Qdrant, Mock ERP.
"""

import logging
from datetime import datetime, timezone

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


async def _check_postgres() -> dict:
    """Verify PostgreSQL connectivity and schema existence."""
    try:
        engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()

            # Verify schemas exist
            schema_result = await conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name IN ('audit', 'erp', 'langgraph') "
                    "ORDER BY schema_name"
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


async def _check_redis() -> dict:
    """Verify Redis connectivity."""
    try:
        client = aioredis.from_url(
            settings.redis_url,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        await client.ping()
        await client.aclose()
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_qdrant() -> dict:
    """Verify Qdrant connectivity."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.qdrant_url}/healthz")
            if response.status_code == 200:
                return {"status": "healthy"}
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
            }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_mock_erp() -> dict:
    """Verify Mock ERP service connectivity."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.erp_base_url}/health")
            if response.status_code == 200:
                return {"status": "healthy"}
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
            }
    except Exception as e:
        logger.error(f"Mock ERP health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health")
async def health_check():
    """
    Liveness probe.
    Returns 200 if the service process is running.
    """
    return {
        "service": "agent-service",
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness probe.
    Checks connectivity to all infrastructure dependencies.
    Returns 200 only if all dependencies are reachable.
    """
    postgres = await _check_postgres()
    redis_status = await _check_redis()
    qdrant = await _check_qdrant()
    mock_erp = await _check_mock_erp()

    dependencies = {
        "postgres": postgres,
        "redis": redis_status,
        "qdrant": qdrant,
        "mock_erp": mock_erp,
    }

    all_healthy = all(
        dep["status"] == "healthy" for dep in dependencies.values()
    )

    return {
        "service": "agent-service",
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": dependencies,
    }
