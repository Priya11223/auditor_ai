"""
Agent Service - Revalidation Service

Applies human feedback as an overlay on top of the original LLM extraction
and re-runs the mathematical and ERP validation logic.
"""

import logging
import uuid

from app.models.database import HumanFeedback
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class RevalidationService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        feedback_repo: FeedbackRepository,
        validation_service: ValidationService,
    ):
        self.invoice_repo = invoice_repo
        self.feedback_repo = feedback_repo
        self.validation_service = validation_service

    async def apply_feedback_and_revalidate(
        self, invoice_id: uuid.UUID, corrections: list[dict], corrected_by: str
    ) -> dict:
        """
        1. Save human corrections to the append-only table.
        2. Fetch the raw LLM JSON.
        3. Merge the latest corrections into the JSON.
        4. Re-run validation.
        """
        logger.info(f"Applying feedback for invoice {invoice_id} by {corrected_by}")
        
        # 1. Fetch original invoice to get the extracted_raw
        invoice = await self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            return {"error": "Invoice not found"}
            
        base_data = invoice.extracted_raw or {}
        
        # 2. Save the new feedback records
        for c in corrections:
            field_name = c["field_name"]
            new_val = c["corrected_value"]
            
            # Determine original value from base_data if possible
            # Simplified: we just grab it if it's a top-level key
            orig_val = str(base_data.get(field_name, ""))
            
            feedback = HumanFeedback(
                invoice_id=invoice_id,
                field_name=field_name,
                original_value=orig_val,
                corrected_value=new_val,
                corrected_by=corrected_by
            )
            await self.feedback_repo.create(feedback)

        # 3. Fetch ALL latest corrections (including ones submitted in previous sessions)
        latest_feedback = await self.feedback_repo.get_latest_corrections(invoice_id)
        
        # 4. Apply overlay
        # This is a simplified merge. In production, mapping nested line item corrections 
        # requires dot-notation parsing (e.g. "line_items.0.unit_price").
        # For Phase 11, we assume top-level field corrections.
        for field, fb in latest_feedback.items():
            base_data[field] = fb.corrected_value
            
        # 5. Revalidate with the modified data
        result = await self.validation_service.validate_invoice(invoice_id, base_data)
        
        # 6. Mark feedback as processed
        await self.feedback_repo.mark_revalidated(invoice_id)
        
        return result
