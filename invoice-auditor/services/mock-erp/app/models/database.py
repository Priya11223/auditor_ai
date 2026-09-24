"""
Mock ERP Service - SQLAlchemy ORM Models (erp schema)

Four tables:
  - erp.vendors          : Vendor master data
  - erp.purchase_orders  : Purchase order headers
  - erp.po_line_items    : PO line items (one row per line)
  - erp.sku_master       : SKU / product master data

These tables are owned by Mock ERP and accessed by
agent-service ONLY through HTTP APIs.
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import Base


# ============================================================
# erp.vendors
# ============================================================
class Vendor(Base):
    """Vendor master data."""
    __tablename__ = "vendors"
    __table_args__ = (
        UniqueConstraint("vendor_code", name="uq_vendors_code"),
        {"schema": "erp"},
    )

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    vendor_name: Mapped[str] = mapped_column(String(500), nullable=False)
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relationships ---
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="vendor",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Vendor code={self.vendor_code} name={self.vendor_name}>"


# ============================================================
# erp.purchase_orders
# ============================================================
class PurchaseOrder(Base):
    """Purchase order header."""
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("po_number", name="uq_po_number"),
        {"schema": "erp"},
    )

    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    po_number: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("erp.vendors.vendor_id"),
        nullable=False,
    )
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # --- Relationships ---
    vendor: Mapped["Vendor"] = relationship(
        back_populates="purchase_orders",
    )
    line_items: Mapped[list["POLineItem"]] = relationship(
        back_populates="purchase_order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder po={self.po_number} status={self.status}>"


# ============================================================
# erp.po_line_items
# ============================================================
class POLineItem(Base):
    """Individual line item within a purchase order."""
    __tablename__ = "po_line_items"
    __table_args__ = {"schema": "erp"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    po_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("erp.purchase_orders.po_id", ondelete="CASCADE"),
        nullable=False,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    sku_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)

    # --- Relationship ---
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        back_populates="line_items",
    )

    def __repr__(self) -> str:
        return (
            f"<POLineItem line={self.line_number} "
            f"sku={self.sku_code} qty={self.quantity}>"
        )


# ============================================================
# erp.sku_master
# ============================================================
class SKUMaster(Base):
    """SKU / product master data."""
    __tablename__ = "sku_master"
    __table_args__ = (
        UniqueConstraint("sku_code", name="uq_sku_code"),
        {"schema": "erp"},
    )

    sku_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    sku_code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(200))
    standard_price: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False
    )
    unit_of_measure: Mapped[str] = mapped_column(
        String(20), nullable=False, default="EA"
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SKUMaster code={self.sku_code} desc={self.description}>"
