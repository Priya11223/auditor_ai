"""
Agent Service - SQLAlchemy ORM Models (audit schema)

Four tables:
  - audit.invoice_audit     : Main invoice record
  - audit.invoice_line_items: Invoice line items (one row per line)
  - audit.discrepancies     : One row per validation mismatch
  - audit.human_feedback    : Immutable human correction records

Design decisions:
  - All monetary fields use Numeric (never Float)
  - All dates use Date or DateTime(timezone=True)
  - Line items are separate rows, not JSON blobs
  - human_feedback is INSERT-only; originals are never overwritten
  - UUIDs used for all primary keys (server-side generation)
"""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


# ============================================================
# audit.invoice_audit
# ============================================================
class InvoiceAudit(Base):
    """
    Main invoice audit record.
    One row per processed invoice file.
    """
    __tablename__ = "invoice_audit"
    __table_args__ = (
        UniqueConstraint("file_checksum", name="uq_invoice_audit_checksum"),
        {"schema": "audit"},
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    extraction_method: Mapped[str | None] = mapped_column(String(50))
    raw_extracted_text: Mapped[str | None] = mapped_column(Text)
    translated_text: Mapped[str | None] = mapped_column(Text)
    source_language: Mapped[str | None] = mapped_column(String(10))
    translation_confidence: Mapped[float | None] = mapped_column(
        Numeric(5, 4)
    )

    # Extracted invoice fields
    invoice_number: Mapped[str | None] = mapped_column(String(100))
    vendor_name: Mapped[str | None] = mapped_column(String(500))
    po_number: Mapped[str | None] = mapped_column(String(100))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str | None] = mapped_column(String(10))
    total_amount: Mapped[float | None] = mapped_column(Numeric(18, 4))

    # Validation outcome
    validation_status: Mapped[str | None] = mapped_column(
        String(20)
    )  # passed | failed | partial
    recommendation: Mapped[str | None] = mapped_column(
        String(20)
    )  # approve | review | reject

    # Raw extraction snapshot (full LLM output preserved as JSON)
    extracted_raw: Mapped[dict | None] = mapped_column(JSONB)

    # Workflow reference
    thread_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # Timestamps
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relationships ---
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    discrepancies: Mapped[list["Discrepancy"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    feedback: Mapped[list["HumanFeedback"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<InvoiceAudit id={self.invoice_id} "
            f"number={self.invoice_number} "
            f"status={self.recommendation}>"
        )


# ============================================================
# audit.invoice_line_items
# ============================================================
class InvoiceLineItem(Base):
    """
    Individual line item from an invoice.
    One row per line; never stored as a JSON blob.
    """
    __tablename__ = "invoice_line_items"
    __table_args__ = {"schema": "audit"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit.invoice_audit.invoice_id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    item_code: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4))
    unit_price: Mapped[float | None] = mapped_column(Numeric(18, 4))
    line_total: Mapped[float | None] = mapped_column(Numeric(18, 4))

    # --- Relationship ---
    invoice: Mapped["InvoiceAudit"] = relationship(
        back_populates="line_items",
    )

    def __repr__(self) -> str:
        return (
            f"<InvoiceLineItem line={self.line_number} "
            f"item={self.item_code} qty={self.quantity}>"
        )


# ============================================================
# audit.discrepancies
# ============================================================
class Discrepancy(Base):
    """
    One row per validation mismatch between invoice and ERP data.
    """
    __tablename__ = "discrepancies"
    __table_args__ = {"schema": "audit"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit.invoice_audit.invoice_id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_value: Mapped[str | None] = mapped_column(Text)
    erp_value: Mapped[str | None] = mapped_column(Text)
    deviation_pct: Mapped[float | None] = mapped_column(Numeric(10, 4))
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # low | medium | high | critical
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relationship ---
    invoice: Mapped["InvoiceAudit"] = relationship(
        back_populates="discrepancies",
    )

    def __repr__(self) -> str:
        return (
            f"<Discrepancy field={self.field_name} "
            f"severity={self.severity}>"
        )


# ============================================================
# audit.human_feedback
# ============================================================
class HumanFeedback(Base):
    """
    Immutable record of a human correction.
    INSERT-only — originals are never overwritten.
    Multiple corrections per field are allowed (latest corrected_at wins).
    """
    __tablename__ = "human_feedback"
    __table_args__ = {"schema": "audit"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("audit.invoice_audit.invoice_id", ondelete="CASCADE"),
        nullable=False,
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    original_value: Mapped[str | None] = mapped_column(Text)
    corrected_value: Mapped[str | None] = mapped_column(Text)
    corrected_by: Mapped[str] = mapped_column(String(200), nullable=False)
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    revalidated: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # --- Relationship ---
    invoice: Mapped["InvoiceAudit"] = relationship(
        back_populates="feedback",
    )

    def __repr__(self) -> str:
        return (
            f"<HumanFeedback field={self.field_name} "
            f"by={self.corrected_by}>"
        )
