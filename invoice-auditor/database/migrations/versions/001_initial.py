"""Initial schema - audit and ERP tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-09-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # AUDIT SCHEMA TABLES
    # ============================================================

    # --- audit.invoice_audit ---
    op.create_table(
        "invoice_audit",
        sa.Column("invoice_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_checksum", sa.String(64), nullable=False),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("raw_extracted_text", sa.Text, nullable=True),
        sa.Column("translated_text", sa.Text, nullable=True),
        sa.Column("source_language", sa.String(10), nullable=True),
        sa.Column("translation_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("invoice_number", sa.String(100), nullable=True),
        sa.Column("vendor_name", sa.String(500), nullable=True),
        sa.Column("po_number", sa.String(100), nullable=True),
        sa.Column("invoice_date", sa.Date, nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("total_amount", sa.Numeric(18, 4), nullable=True),
        sa.Column("validation_status", sa.String(20), nullable=True),
        sa.Column("recommendation", sa.String(20), nullable=True),
        sa.Column("extracted_raw", JSONB, nullable=True),
        sa.Column("thread_id", UUID(as_uuid=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.UniqueConstraint("file_checksum", name="uq_invoice_audit_checksum"),
        schema="audit",
    )

    # --- audit.invoice_line_items ---
    op.create_table(
        "invoice_line_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", UUID(as_uuid=True), nullable=False),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("item_code", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=True),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("line_total", sa.Numeric(18, 4), nullable=True),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["audit.invoice_audit.invoice_id"],
            ondelete="CASCADE",
        ),
        schema="audit",
    )

    # --- audit.discrepancies ---
    op.create_table(
        "discrepancies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("invoice_value", sa.Text, nullable=True),
        sa.Column("erp_value", sa.Text, nullable=True),
        sa.Column("deviation_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["audit.invoice_audit.invoice_id"],
            ondelete="CASCADE",
        ),
        schema="audit",
    )

    # --- audit.human_feedback ---
    op.create_table(
        "human_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("invoice_id", UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("original_value", sa.Text, nullable=True),
        sa.Column("corrected_value", sa.Text, nullable=True),
        sa.Column("corrected_by", sa.String(200), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.Column("revalidated", sa.Boolean, nullable=False,
                   server_default=sa.text("false")),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["audit.invoice_audit.invoice_id"],
            ondelete="CASCADE",
        ),
        schema="audit",
    )

    # ============================================================
    # ERP SCHEMA TABLES
    # ============================================================

    # --- erp.vendors ---
    op.create_table(
        "vendors",
        sa.Column("vendor_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("vendor_name", sa.String(500), nullable=False),
        sa.Column("vendor_code", sa.String(50), nullable=False),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.UniqueConstraint("vendor_code", name="uq_vendors_code"),
        schema="erp",
    )

    # --- erp.purchase_orders ---
    op.create_table(
        "purchase_orders",
        sa.Column("po_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("po_number", sa.String(100), nullable=False),
        sa.Column("vendor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("po_date", sa.Date, nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.UniqueConstraint("po_number", name="uq_po_number"),
        sa.ForeignKeyConstraint(
            ["vendor_id"],
            ["erp.vendors.vendor_id"],
        ),
        schema="erp",
    )

    # --- erp.po_line_items ---
    op.create_table(
        "po_line_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("po_id", UUID(as_uuid=True), nullable=False),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("sku_code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("line_total", sa.Numeric(18, 4), nullable=False),
        sa.ForeignKeyConstraint(
            ["po_id"],
            ["erp.purchase_orders.po_id"],
            ondelete="CASCADE",
        ),
        schema="erp",
    )

    # --- erp.sku_master ---
    op.create_table(
        "sku_master",
        sa.Column("sku_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("sku_code", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("standard_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_of_measure", sa.String(20), nullable=False,
                   server_default="EA"),
        sa.Column("active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.func.now()),
        sa.UniqueConstraint("sku_code", name="uq_sku_code"),
        schema="erp",
    )

    # ============================================================
    # INDEXES
    # ============================================================
    op.create_index(
        "ix_invoice_audit_recommendation",
        "invoice_audit",
        ["recommendation"],
        schema="audit",
    )
    op.create_index(
        "ix_invoice_audit_invoice_number",
        "invoice_audit",
        ["invoice_number"],
        schema="audit",
    )
    op.create_index(
        "ix_discrepancies_invoice_id",
        "discrepancies",
        ["invoice_id"],
        schema="audit",
    )
    op.create_index(
        "ix_human_feedback_invoice_id",
        "human_feedback",
        ["invoice_id"],
        schema="audit",
    )
    op.create_index(
        "ix_line_items_invoice_id",
        "invoice_line_items",
        ["invoice_id"],
        schema="audit",
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("po_line_items", schema="erp")
    op.drop_table("purchase_orders", schema="erp")
    op.drop_table("sku_master", schema="erp")
    op.drop_table("vendors", schema="erp")
    op.drop_table("human_feedback", schema="audit")
    op.drop_table("discrepancies", schema="audit")
    op.drop_table("invoice_line_items", schema="audit")
    op.drop_table("invoice_audit", schema="audit")
