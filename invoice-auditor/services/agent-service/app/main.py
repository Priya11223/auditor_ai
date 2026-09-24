"""
Agent Service - FastAPI Application Entry Point

Phase 1: Minimal application with health check endpoints.
"""

import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.errors import register_exception_handlers
from app.clients.http_client import start_http_client, stop_http_client
from app.config.settings import settings

# --- Structured Logging Setup ---
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent-service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Invoice Audit Agent Service",
        description="Agentic Invoice Audit and Validation Platform",
        version="0.1.0",
    )

    # --- Register Routers ---
    app.include_router(health_router)

    # --- Register Exception Handlers ---
    register_exception_handlers(app)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Agent Service starting up...")
        logger.info(f"PostgreSQL: {settings.database_url.split('@')[-1]}")
        logger.info(f"Redis: {settings.redis_url}")
        logger.info(f"Qdrant: {settings.qdrant_url}")
        logger.info(f"Mock ERP: {settings.erp_base_url}")
        logger.info(f"Incoming dir: {settings.incoming_dir}")
        logger.info(f"Reports dir: {settings.reports_dir}")
        
        await start_http_client()
        logger.info("HTTP client initialized.")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Agent Service shutting down...")
        await stop_http_client()
        logger.info("HTTP client closed.")

    return app


app = create_app()
