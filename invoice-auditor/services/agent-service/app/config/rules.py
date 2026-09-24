"""
Agent Service - Rules Configuration Loader

Loads and validates the business rules from configs/rules.yaml
into Pydantic models for type-safe access.
"""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Fallback path if deployed directly instead of via docker-compose
DEFAULT_RULES_PATH = Path("/configs/rules.yaml")
if not DEFAULT_RULES_PATH.exists():
    # Relative path for local development
    DEFAULT_RULES_PATH = Path(__file__).parent.parent.parent.parent.parent / "configs" / "rules.yaml"


class MonitorRules(BaseModel):
    poll_interval_seconds: int
    stability_checks: int
    max_file_size_mb: int
    supported_extensions: list[str]


class ToleranceRules(BaseModel):
    threshold_pct: float
    severity_above: str


class Tolerances(BaseModel):
    quantity: ToleranceRules
    unit_price: ToleranceRules
    total_amount: ToleranceRules


class RecommendationRules(BaseModel):
    missing_required_field: str
    missing_critical_field: str
    arithmetic_failure: str
    erp_mismatch_high: str
    erp_mismatch_critical: str
    erp_unavailable: str
    all_passed: str


class TranslationRules(BaseModel):
    min_text_length_for_detection: int
    cache_ttl_seconds: int


class RAGRules(BaseModel):
    max_reflection_retries: int
    relevance_threshold: float
    top_k: int
    chunk_size: int
    chunk_overlap: int


class RulesConfig(BaseModel):
    """Strongly typed representation of rules.yaml."""
    required_fields: dict[str, bool]
    line_item_required_fields: dict[str, bool]
    critical_fields: list[str]
    arithmetic_tolerance_pct: float
    tolerances: Tolerances
    recommendation: RecommendationRules
    translation: TranslationRules
    monitor: MonitorRules
    rag: RAGRules


def load_rules(path: Path = DEFAULT_RULES_PATH) -> RulesConfig:
    """Load the rules.yaml file into a RulesConfig model."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return RulesConfig(**data)
    except Exception as e:
        logger.error(f"Failed to load rules from {path}: {e}")
        raise


# Singleton rules configuration instance
try:
    rules = load_rules()
except Exception:
    # Allows imports to succeed even if rules aren't found at import time (e.g. tests)
    rules = None  # type: ignore
