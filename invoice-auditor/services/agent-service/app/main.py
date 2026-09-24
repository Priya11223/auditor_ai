"""
Agent Service - FastAPI Application Entry Point

Phase 1: Minimal application with health check endpoints.
"""

import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.routes.feedback import router as feedback_router
from app.api.errors import register_exception_handlers
from app.clients.http_client import start_http_client, stop_http_client
from app.clients.redis_client import start_redis, stop_redis
from app.config.settings import settings
from app.worker.file_monitor import start_file_monitor

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
    app.include_router(feedback_router)

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
        
        await start_redis()
        logger.info("Redis pool initialized.")
        
        # Start the file monitor in the background
        monitor_dir = "/app/data/incoming" if settings.environment == "production" else "./incoming"
        app.state.monitor_task = asyncio.create_task(start_file_monitor(monitor_dir))
        logger.info(f"File monitor task started watching {monitor_dir}")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Agent Service shutting down...")
        
        # Cancel the file monitor task
        if hasattr(app.state, "monitor_task"):
            app.state.monitor_task.cancel()
            logger.info("File monitor task cancelled.")
            
        await stop_http_client()
        logger.info("HTTP client closed.")
        
        await stop_redis()
        logger.info("Redis pool closed.")

    return app


app = create_app()
