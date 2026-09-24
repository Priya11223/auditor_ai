"""
Invoice Repository - CRUD operations for audit.invoice_audit

Handles:
  - Creating new invoice records
  - Checking for duplicate checksums
  - Updating extraction/validation/recommendation fields
  - Querying invoices by status, id, etc.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import InvoiceAudit


class InvoiceRepository:
    """Repository for audit.invoice_audit table."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, invoice: InvoiceAudit) -> InvoiceAudit:
        """Insert a new invoice audit record."""
        self.session.add(invoice)
        await self.session.flush()
        return invoice

    async def get_by_id(self, invoice_id: uuid.UUID) -> InvoiceAudit | None:
        """Fetch an invoice by its UUID (with relationships eager-loaded)."""
        stmt = select(InvoiceAudit).where(
            InvoiceAudit.invoice_id == invoice_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_checksum(self, checksum: str) -> InvoiceAudit | None:
        """Check if a file with this checksum has already been processed."""
        stmt = select(InvoiceAudit).where(
            InvoiceAudit.file_checksum == checksum
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_checksum(self, checksum: str) -> bool:
        """Fast duplicate check — returns True if checksum already exists."""
        stmt = select(InvoiceAudit.invoice_id).where(
            InvoiceAudit.file_checksum == checksum
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_extraction(
        self,
        invoice_id: uuid.UUID,
        raw_text: str,
        extraction_method: str,
    ) -> None:
        """Update extraction results after text extraction phase."""
        stmt = (
            update(InvoiceAudit)
            .where(InvoiceAudit.invoice_id == invoice_id)
            .values(
                raw_extracted_text=raw_text,
                extraction_method=extraction_method,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)

    async def update_translation(
        self,
        invoice_id: uuid.UUID,
        source_language: str,
        translated_text: str | None,
        translation_confidence: float | None,
    ) -> None:
        """Update translation results."""
        stmt = (
            update(InvoiceAudit)
            .where(InvoiceAudit.invoice_id == invoice_id)
            .values(
                source_language=source_language,
                translated_text=translated_text,
                translation_confidence=translation_confidence,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)

    async def update_parsed_fields(
        self,
        invoice_id: uuid.UUID,
        invoice_number: str | None,
        vendor_name: str | None,
        po_number: str | None,
        invoice_date: str | None,
        currency: str | None,
        total_amount: float | None,
        extracted_raw: dict | None,
    ) -> None:
        """Update structured parsed invoice fields."""
        stmt = (
            update(InvoiceAudit)
            .where(InvoiceAudit.invoice_id == invoice_id)
            .values(
                invoice_number=invoice_number,
                vendor_name=vendor_name,
                po_number=po_number,
                invoice_date=invoice_date,
                currency=currency,
                total_amount=total_amount,
                extracted_raw=extracted_raw,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)

    async def update_validation_result(
        self,
        invoice_id: uuid.UUID,
        validation_status: str,
        recommendation: str,
    ) -> None:
        """Update the validation outcome and recommendation."""
        stmt = (
            update(InvoiceAudit)
            .where(InvoiceAudit.invoice_id == invoice_id)
            .values(
                validation_status=validation_status,
                recommendation=recommendation,
                processed_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)

    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InvoiceAudit]:
        """List invoices with pagination, most recent first."""
        stmt = (
            select(InvoiceAudit)
            .order_by(InvoiceAudit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_recommendation(
        self,
        recommendation: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InvoiceAudit]:
        """List invoices filtered by recommendation status."""
        stmt = (
            select(InvoiceAudit)
            .where(InvoiceAudit.recommendation == recommendation)
            .order_by(InvoiceAudit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
