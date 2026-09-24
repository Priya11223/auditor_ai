"""
Agent Service - Sync Repositories (For Workflow Nodes)

Helper functions to get synchronous instances of repositories 
for use within the async workflow nodes without requiring FastAPI Depends.
"""

from app.models.database import AsyncSessionLocal
from app.repositories.discrepancy_repository import DiscrepancyRepository
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.line_item_repository import LineItemRepository

def get_invoice_repo_sync() -> InvoiceRepository:
    return InvoiceRepository(AsyncSessionLocal())

def get_line_item_repo_sync() -> LineItemRepository:
    return LineItemRepository(AsyncSessionLocal())

def get_discrepancy_repo_sync() -> DiscrepancyRepository:
    return DiscrepancyRepository(AsyncSessionLocal())
