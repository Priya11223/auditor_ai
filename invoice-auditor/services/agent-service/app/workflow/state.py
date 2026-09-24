"""
Agent Service - Workflow State

Defines the state schema for the LangGraph orchestrator.
This TypedDict serves as the single source of truth as the invoice
moves through the pipeline.
"""

import uuid
from typing import Any, Optional, TypedDict


class InvoiceState(TypedDict):
    # Phase 5 (File Service)
    invoice_id: uuid.UUID
    file_path: str
    file_type: str
    is_duplicate: bool
    checksum: str
    
    # Phase 6 (Extraction)
    raw_text: Optional[str]
    extraction_method: Optional[str]
    
    # Phase 7 (Translation)
    source_language: Optional[str]
    translated_text: Optional[str]
    
    # Phase 8 (LLM Parsing)
    parsed_data: Optional[dict[str, Any]]
    
    # Phase 10 (Validation)
    validation_status: Optional[str]
    recommendation: Optional[str]
    discrepancies: Optional[list[dict[str, Any]]]
    
    # Global Error tracking
    error: Optional[str]
