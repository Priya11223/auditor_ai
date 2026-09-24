"""
Mock ERP Service - FastAPI Application Entry Point

Phase 1: Minimal application with health check endpoints.
Serves as the HTTP boundary for ERP data access.
"""

import logging
import os

from fastapi import FastAPI

from app.api.health import router as health_router

# --- Structured Logging Setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mock-erp")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Mock ERP Service",
        description="Mock ERP HTTP API for invoice audit validation",
        version="0.1.0",
    )

    # --- Register Routers ---
    app.include_router(health_router)
    
    from app.api.routes import router as api_router
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup_event():
        logger.info("Mock ERP Service starting up...")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Mock ERP Service shutting down...")

    return app


app = create_app()
