"""
Agent Service - LLM Extraction Service

Uses AWS Bedrock to extract structured data from unstructured text,
validates the output using Pydantic, and saves it to the database.
"""

import logging
import uuid
from typing import Any

from pydantic import ValidationError

from app.clients.bedrock_client import get_bedrock_client
from app.models.database import InvoiceLineItem
from app.models.extraction_schemas import ExtractedInvoice
from app.repositories.invoice_repository import InvoiceRepository
from app.repositories.line_item_repository import LineItemRepository

logger = logging.getLogger(__name__)


class LLMExtractionService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        line_item_repo: LineItemRepository,
    ):
        self.invoice_repo = invoice_repo
        self.line_item_repo = line_item_repo
        self.bedrock = get_bedrock_client()

    async def extract_structured_data(self, text: str, invoice_id: uuid.UUID) -> dict[str, Any]:
        """
        Extract structured data via LLM tool-calling, validate it,
        and update the audit tables.
        """
        error_msg = None
        parsed_data = None

        if not text:
            error_msg = "No text provided for extraction"
            return {"parsed_data": None, "error": error_msg}

        logger.info(f"Extracting structured data for invoice {invoice_id}")
        
        # 1. Call Bedrock with the Pydantic JSON schema
        raw_json = await self.bedrock.extract_json(
            text=text,
            schema=ExtractedInvoice.model_json_schema()
        )

        if raw_json is None:
            error_msg = "Bedrock failed to return structured JSON data"
            logger.error(error_msg)
        else:
            # 2. Validate with Pydantic
            try:
                extracted = ExtractedInvoice.model_validate(raw_json)
                parsed_data = extracted.model_dump(mode="json")
                
                # 3. Save to database
                await self._save_to_db(invoice_id, extracted, raw_json)
                logger.info(f"Successfully extracted and saved data for invoice {invoice_id}")

            except ValidationError as e:
                error_msg = f"LLM returned invalid data schema: {str(e)}"
                logger.error(error_msg)
                
                # Update DB with the raw attempt even if it failed validation
                await self.invoice_repo.update_parsed_fields(
                    invoice_id=invoice_id,
                    invoice_number=None,
                    vendor_name=None,
                    po_number=None,
                    invoice_date=None,
                    currency=None,
                    total_amount=None,
                    extracted_raw=raw_json,
                )
            except Exception as e:
                error_msg = f"Database error saving extracted data: {str(e)}"
                logger.error(error_msg)

        return {
            "parsed_data": parsed_data,
            "error": error_msg,
        }

    async def _save_to_db(self, invoice_id: uuid.UUID, extracted: ExtractedInvoice, raw_json: dict):
        """Save the parsed data to the relational tables."""
        
        # Format the date if it exists
        date_str = None
        if extracted.invoice_date:
            date_str = extracted.invoice_date

        # Update the main invoice record
        await self.invoice_repo.update_parsed_fields(
            invoice_id=invoice_id,
            invoice_number=extracted.invoice_number,
            vendor_name=extracted.vendor_name,
            po_number=extracted.po_number,
            invoice_date=date_str,
            currency=extracted.currency,
            total_amount=float(extracted.total_amount) if extracted.total_amount else None,
            extracted_raw=raw_json,
        )

        # First, clear any existing line items (in case of re-processing)
        await self.line_item_repo.delete_by_invoice_id(invoice_id)

        # Insert line items
        if extracted.line_items:
            db_line_items = []
            for item in extracted.line_items:
                db_line_items.append(
                    InvoiceLineItem(
                        invoice_id=invoice_id,
                        line_number=item.line_number,
                        item_code=item.item_code,
                        description=item.description,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        line_total=item.line_total,
                    )
                )
            await self.line_item_repo.create_many(db_line_items)
