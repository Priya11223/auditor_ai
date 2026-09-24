"""
Streamlit UI - API Client

Helper functions to fetch data from the Agent Service over HTTP.
"""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Fallback to localhost if running outside Docker for local dev
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:8000")


def get_pending_invoices() -> list[dict[str, Any]]:
    """Fetch invoices that require human review."""
    url = f"{AGENT_SERVICE_URL}/api/v1/invoices/pending"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch pending invoices: {e}")
        raise

def get_invoice_details(invoice_id: str) -> dict[str, Any]:
    """Fetch full details and discrepancies for a specific invoice."""
    url = f"{AGENT_SERVICE_URL}/api/v1/invoices/{invoice_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch invoice details for {invoice_id}: {e}")
        raise

def submit_feedback(invoice_id: str, payload: dict) -> dict[str, Any]:
    """Submit human corrections and re-trigger validation."""
    url = f"{AGENT_SERVICE_URL}/api/v1/invoices/{invoice_id}/feedback"
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to submit feedback for {invoice_id}: {e}")
        raise
