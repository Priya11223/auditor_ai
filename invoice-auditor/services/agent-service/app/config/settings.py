"""
Agent Service - Configuration
Loads all settings from environment variables using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Database ---
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres:5432/invoice_auditor",
        description="Async PostgreSQL connection string",
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/invoice_auditor",
        description="Sync PostgreSQL connection string (for Alembic)",
    )

    # --- Redis ---
    redis_url: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection string",
    )

    # --- Qdrant ---
    qdrant_url: str = Field(
        default="http://qdrant:6333",
        description="Qdrant HTTP endpoint",
    )
    qdrant_collection: str = Field(
        default="invoices",
        description="Qdrant collection name",
    )

    # --- Mock ERP ---
    erp_base_url: str = Field(
        default="http://mock-erp:8001",
        description="Mock ERP service base URL",
    )

    # --- AWS Bedrock ---
    aws_region: str = Field(default="us-east-1")
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0"
    )

    # --- Paths ---
    incoming_dir: str = Field(
        default="/incoming",
        description="Directory to watch for new invoice files",
    )
    reports_dir: str = Field(
        default="/reports",
        description="Directory for generated reports",
    )

    # --- Logging ---
    log_level: str = Field(default="INFO")

    model_config = {"env_file": ".env", "extra": "ignore"}


# Singleton settings instance
settings = Settings()
