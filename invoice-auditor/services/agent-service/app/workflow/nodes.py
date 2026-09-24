"""
Agent Service - Workflow Nodes

Defines the individual LangGraph nodes that wrap our core services.
"""

import logging

from app.api.deps_sync import (
    get_discrepancy_repo_sync,
    get_invoice_repo_sync,
    get_line_item_repo_sync,
)
from app.services.extraction_service import ExtractionService
from app.services.llm_extraction_service import LLMExtractionService
from app.services.translation_service import TranslationService
from app.services.validation_service import ValidationService
from app.workflow.state import InvoiceState

logger = logging.getLogger(__name__)


async def extract_node(state: InvoiceState) -> InvoiceState:
    """Extract raw text from the file."""
    logger.info(f"[Node: Extract] Processing {state['invoice_id']}")
    
    if state.get("error"):
        return state

    repo = get_invoice_repo_sync()
    service = ExtractionService(repo)
    
    result = await service.extract_text(
        file_path=state["file_path"],
        file_type=state["file_type"],
        invoice_id=state["invoice_id"]
    )
    
    state.update(result)
    return state


async def translate_node(state: InvoiceState) -> InvoiceState:
    """Detect language and translate to English if needed."""
    logger.info(f"[Node: Translate] Processing {state['invoice_id']}")
    
    if state.get("error"):
        return state

    repo = get_invoice_repo_sync()
    service = TranslationService(repo)
    
    result = await service.translate_if_needed(
        raw_text=state.get("raw_text", ""),
        invoice_id=state["invoice_id"]
    )
    
    state.update(result)
    return state


async def parse_node(state: InvoiceState) -> InvoiceState:
    """Parse text into structured JSON using LLM."""
    logger.info(f"[Node: Parse] Processing {state['invoice_id']}")
    
    if state.get("error"):
        return state

    repo = get_invoice_repo_sync()
    line_repo = get_line_item_repo_sync()
    service = LLMExtractionService(repo, line_repo)
    
    # Use translated text if present, otherwise raw text
    text_to_parse = state.get("translated_text") or state.get("raw_text")
    
    result = await service.extract_structured_data(
        text=text_to_parse,
        invoice_id=state["invoice_id"]
    )
    
    state.update(result)
    return state


async def validate_node(state: InvoiceState) -> InvoiceState:
    """Run business validation and ERP checks."""
    logger.info(f"[Node: Validate] Processing {state['invoice_id']}")
    
    if state.get("error"):
        return state

    repo = get_invoice_repo_sync()
    disc_repo = get_discrepancy_repo_sync()
    service = ValidationService(repo, disc_repo)
    
    parsed_data = state.get("parsed_data")
    
    if not parsed_data:
        state["error"] = "Cannot validate without parsed data."
        return state
        
    result = await service.validate_invoice(
        invoice_id=state["invoice_id"],
        parsed_data=parsed_data
    )
    
    state.update(result)
    return state
