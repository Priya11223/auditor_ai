"""
Agent Service - Feedback API Routes

Endpoints for the UI to submit human corrections and re-trigger validation.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_discrepancy_repo,
    get_feedback_repo,
    get_invoice_repo,
    get_line_item_repo,
)
from app.models.api_schemas import FeedbackSubmitRequest, ValidationStateResponse
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.services.revalidation_service import RevalidationService
from app.services.validation_service import ValidationService

router = APIRouter(prefix="/api/v1/invoices", tags=["feedback"])


async def get_revalidation_service(
    invoice_repo: InvoiceRepository = Depends(get_invoice_repo),
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
    discrepancy_repo=Depends(get_discrepancy_repo),
) -> RevalidationService:
    """Dependency injection for the RevalidationService."""
    validation_service = ValidationService(invoice_repo, discrepancy_repo)
    return RevalidationService(invoice_repo, feedback_repo, validation_service)


@router.get("/pending")
async def list_pending_invoices(
    invoice_repo: InvoiceRepository = Depends(get_invoice_repo),
) -> list[dict[str, Any]]:
    """List all invoices that require human review."""
    
    # In a real app we'd paginate this
    reviews = await invoice_repo.list_by_recommendation("review", limit=50)
    rejects = await invoice_repo.list_by_recommendation("reject", limit=50)
    
    combined = reviews + rejects
    return [
        {
            "invoice_id": str(i.invoice_id),
            "invoice_number": i.invoice_number,
            "vendor_name": i.vendor_name,
            "total_amount": float(i.total_amount) if i.total_amount else None,
            "validation_status": i.validation_status,
            "recommendation": i.recommendation,
            "created_at": i.created_at.isoformat(),
        }
        for i in sorted(combined, key=lambda x: x.created_at, reverse=True)
    ]


@router.get("/{invoice_id}")
async def get_invoice_details(
    invoice_id: uuid.UUID,
    invoice_repo: InvoiceRepository = Depends(get_invoice_repo),
    discrepancy_repo = Depends(get_discrepancy_repo),
) -> dict[str, Any]:
    """Fetch full details of an invoice for human review."""
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    discrepancies = await discrepancy_repo.get_by_invoice_id(invoice_id)
    
    return {
        "invoice_id": str(invoice.invoice_id),
        "file_path": invoice.file_path,
        "file_type": invoice.file_type,
        "validation_status": invoice.validation_status,
        "recommendation": invoice.recommendation,
        "extracted_raw": invoice.extracted_raw or {},
        "discrepancies": [
            {
                "field": d.field_name,
                "severity": d.severity,
                "deviation_pct": float(d.deviation_pct) if d.deviation_pct else None,
            }
            for d in discrepancies
        ]
    }


@router.post("/{invoice_id}/feedback", response_model=ValidationStateResponse)
async def submit_feedback(
    invoice_id: uuid.UUID,
    payload: FeedbackSubmitRequest,
    revalidation_svc: RevalidationService = Depends(get_revalidation_service),
):
    """
    Submit human corrections for specific fields on an invoice.
    This saves the feedback immutably and re-triggers validation.
    """
    corrections_list = [
        {"field_name": c.field_name, "corrected_value": c.corrected_value}
        for c in payload.corrections
    ]
    
    result = await revalidation_svc.apply_feedback_and_revalidate(
        invoice_id=invoice_id,
        corrections=corrections_list,
        corrected_by=payload.corrected_by
    )
    
    if "error" in result and result["error"] == "Invoice not found":
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    return result
