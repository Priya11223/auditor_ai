"""
Agent Service - API Schemas

Pydantic models for incoming HTTP requests and outgoing HTTP responses
for the Agent Service API (used by the Streamlit UI).
"""

import uuid
from typing import Optional

from pydantic import BaseModel, Field


class CorrectionItem(BaseModel):
    field_name: str = Field(..., description="The name of the field being corrected (e.g., 'total_amount')")
    corrected_value: str = Field(..., description="The new human-provided value as a string")


class FeedbackSubmitRequest(BaseModel):
    corrected_by: str = Field(..., description="Email or ID of the human auditor")
    corrections: list[CorrectionItem] = Field(..., description="List of corrections to apply")


class DiscrepancyResponse(BaseModel):
    field: str
    severity: str


class ValidationStateResponse(BaseModel):
    validation_status: str
    recommendation: str
    discrepancies: list[DiscrepancyResponse]
    error: Optional[str] = None
