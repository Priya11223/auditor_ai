"""
Agent Service - Validation Service

Implements the core business rules engine. Performs mathematical validation
and compares extracted invoice data against the Mock ERP master data.
Generates discrepancy records based on configurable tolerances.
"""

import logging
import uuid
from decimal import Decimal
from typing import Any, Optional

from app.clients.erp_client import ERPClient
from app.config.rules import rules
from app.models.database import Discrepancy
from app.models.extraction_schemas import ExtractedInvoice, ExtractedLineItem
from app.repositories.discrepancy_repository import DiscrepancyRepository
from app.repositories.invoice_repository import InvoiceRepository

logger = logging.getLogger(__name__)


class ValidationService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        discrepancy_repo: DiscrepancyRepository,
    ):
        self.invoice_repo = invoice_repo
        self.discrepancy_repo = discrepancy_repo
        self.erp_client = ERPClient()

    async def validate_invoice(self, invoice_id: uuid.UUID, parsed_data: dict[str, Any]) -> dict:
        """
        Run all validation checks and update the database with discrepancies and final status.
        """
        logger.info(f"Starting validation for invoice {invoice_id}")
        
        # Clear previous discrepancies in case of re-validation
        await self.discrepancy_repo.delete_by_invoice_id(invoice_id)
        
        discrepancies: list[Discrepancy] = []
        error_msg = None

        if not parsed_data:
            error_msg = "No parsed data available for validation"
            return self._finalize(invoice_id, "failed", "reject", [], error_msg)

        try:
            # Parse the dict back into our Pydantic model for strict typing
            invoice = ExtractedInvoice.model_validate(parsed_data)
        except Exception as e:
            error_msg = f"Failed to validate parsed data schema: {e}"
            logger.error(error_msg)
            return self._finalize(invoice_id, "failed", "reject", [], error_msg)

        # 1. Missing Required Fields
        discrepancies.extend(self._check_required_fields(invoice_id, invoice))

        # 2. Arithmetic Validation
        discrepancies.extend(self._check_arithmetic(invoice_id, invoice))

        # 3. ERP Validation (PO Match)
        try:
            if invoice.po_number:
                erp_discrepancies = await self._check_erp_match(invoice_id, invoice)
                discrepancies.extend(erp_discrepancies)
            else:
                discrepancies.append(
                    Discrepancy(
                        invoice_id=invoice_id,
                        field_name="po_number",
                        invoice_value=None,
                        erp_value=None,
                        severity=rules.recommendation.missing_critical_field,
                    )
                )
        except Exception as e:
            logger.error(f"ERP Validation failed for {invoice_id}: {e}")
            discrepancies.append(
                Discrepancy(
                    invoice_id=invoice_id,
                    field_name="erp_connection",
                    severity=rules.recommendation.erp_unavailable,
                )
            )

        # 4. Save Discrepancies
        if discrepancies:
            await self.discrepancy_repo.create_many(discrepancies)

        # 5. Determine Final Status and Recommendation
        validation_status, recommendation = self._calculate_recommendation(discrepancies)
        
        return await self._finalize(
            invoice_id, 
            validation_status, 
            recommendation, 
            discrepancies
        )

    async def _finalize(
        self, 
        invoice_id: uuid.UUID, 
        status: str, 
        recommendation: str, 
        discrepancies: list[Discrepancy], 
        error: Optional[str] = None
    ) -> dict:
        """Update DB and return the workflow state."""
        await self.invoice_repo.update_validation_result(
            invoice_id=invoice_id,
            validation_status=status,
            recommendation=recommendation
        )
        
        return {
            "validation_status": status,
            "recommendation": recommendation,
            "discrepancies": [{"field": d.field_name, "severity": d.severity} for d in discrepancies],
            "error": error
        }

    def _check_required_fields(self, invoice_id: uuid.UUID, invoice: ExtractedInvoice) -> list[Discrepancy]:
        discrepancies = []
        for field, is_required in rules.required_fields.items():
            if is_required and not getattr(invoice, field, None):
                severity = (
                    rules.recommendation.missing_critical_field 
                    if field in rules.critical_fields 
                    else rules.recommendation.missing_required_field
                )
                discrepancies.append(
                    Discrepancy(
                        invoice_id=invoice_id,
                        field_name=field,
                        severity=severity,
                    )
                )
        return discrepancies

    def _check_arithmetic(self, invoice_id: uuid.UUID, invoice: ExtractedInvoice) -> list[Discrepancy]:
        discrepancies = []
        calculated_total = Decimal('0.0')
        tolerance_pct = Decimal(str(rules.arithmetic_tolerance_pct))

        for item in invoice.line_items:
            # Check line totals (qty * price)
            if item.quantity is not None and item.unit_price is not None:
                expected_line_total = item.quantity * item.unit_price
                if item.line_total is not None:
                    diff = abs(expected_line_total - item.line_total)
                    if expected_line_total > 0:
                        deviation = (diff / expected_line_total) * 100
                        if deviation > tolerance_pct:
                            discrepancies.append(
                                Discrepancy(
                                    invoice_id=invoice_id,
                                    field_name=f"line_total_math_L{item.line_number}",
                                    invoice_value=str(item.line_total),
                                    erp_value=str(expected_line_total),
                                    deviation_pct=deviation,
                                    severity=rules.recommendation.arithmetic_failure,
                                )
                            )
                
                # Accumulate for invoice total
                calculated_total += item.line_total if item.line_total else expected_line_total

        # Check invoice total
        if invoice.total_amount is not None:
            diff = abs(calculated_total - invoice.total_amount)
            if calculated_total > 0:
                deviation = (diff / calculated_total) * 100
                if deviation > tolerance_pct:
                    discrepancies.append(
                        Discrepancy(
                            invoice_id=invoice_id,
                            field_name="total_amount_math",
                            invoice_value=str(invoice.total_amount),
                            erp_value=str(calculated_total),
                            deviation_pct=deviation,
                            severity=rules.recommendation.arithmetic_failure,
                        )
                    )

        return discrepancies

    async def _check_erp_match(self, invoice_id: uuid.UUID, invoice: ExtractedInvoice) -> list[Discrepancy]:
        discrepancies = []
        
        # Fetch PO from Mock ERP
        po = await self.erp_client.get_po(invoice.po_number)
        if not po:
            return [
                Discrepancy(
                    invoice_id=invoice_id,
                    field_name="po_number",
                    invoice_value=invoice.po_number,
                    severity=rules.recommendation.missing_critical_field,
                )
            ]

        # Check Vendor
        if invoice.vendor_name and po.vendor.vendor_name.lower() not in invoice.vendor_name.lower():
            # Soft match failure
            discrepancies.append(
                Discrepancy(
                    invoice_id=invoice_id,
                    field_name="vendor_name",
                    invoice_value=invoice.vendor_name,
                    erp_value=po.vendor.vendor_name,
                    severity="medium",
                )
            )

        # Check Total Amount Tolerance
        if invoice.total_amount:
            deviation = self._calculate_deviation(invoice.total_amount, po.total_amount)
            threshold = Decimal(str(rules.tolerances.total_amount.threshold_pct))
            if deviation > threshold:
                discrepancies.append(
                    Discrepancy(
                        invoice_id=invoice_id,
                        field_name="total_amount_erp",
                        invoice_value=str(invoice.total_amount),
                        erp_value=str(po.total_amount),
                        deviation_pct=deviation,
                        severity=rules.tolerances.total_amount.severity_above,
                    )
                )

        # Compare line items by SKU (if extracted) or assume order matches
        erp_lines = {str(item.sku_code): item for item in po.line_items}
        
        for inv_line in invoice.line_items:
            # We attempt matching by item_code if present
            erp_match = erp_lines.get(str(inv_line.item_code))
            
            if not erp_match:
                discrepancies.append(
                    Discrepancy(
                        invoice_id=invoice_id,
                        field_name=f"item_code_L{inv_line.line_number}",
                        invoice_value=str(inv_line.item_code),
                        severity="high",
                    )
                )
                continue
                
            # Check Quantity Tolerance
            if inv_line.quantity:
                deviation = self._calculate_deviation(inv_line.quantity, erp_match.quantity)
                threshold = Decimal(str(rules.tolerances.quantity.threshold_pct))
                if deviation > threshold:
                    discrepancies.append(
                        Discrepancy(
                            invoice_id=invoice_id,
                            field_name=f"quantity_L{inv_line.line_number}",
                            invoice_value=str(inv_line.quantity),
                            erp_value=str(erp_match.quantity),
                            deviation_pct=deviation,
                            severity=rules.tolerances.quantity.severity_above,
                        )
                    )

            # Check Unit Price Tolerance
            if inv_line.unit_price:
                deviation = self._calculate_deviation(inv_line.unit_price, erp_match.unit_price)
                threshold = Decimal(str(rules.tolerances.unit_price.threshold_pct))
                if deviation > threshold:
                    discrepancies.append(
                        Discrepancy(
                            invoice_id=invoice_id,
                            field_name=f"unit_price_L{inv_line.line_number}",
                            invoice_value=str(inv_line.unit_price),
                            erp_value=str(erp_match.unit_price),
                            deviation_pct=deviation,
                            severity=rules.tolerances.unit_price.severity_above,
                        )
                    )

        return discrepancies

    def _calculate_deviation(self, invoice_val: Decimal, erp_val: Decimal) -> Decimal:
        """Calculate percentage deviation."""
        if erp_val == 0:
            return Decimal('100.0') if invoice_val != 0 else Decimal('0.0')
        return (abs(invoice_val - erp_val) / erp_val) * 100

    def _calculate_recommendation(self, discrepancies: list[Discrepancy]) -> tuple[str, str]:
        """
        Determine validation status (passed, failed, partial) 
        and recommendation (approve, review, reject) based on highest severity.
        """
        if not discrepancies:
            return "passed", rules.recommendation.all_passed

        has_critical = any(d.severity == "critical" for d in discrepancies)
        has_high = any(d.severity == "high" for d in discrepancies)
        
        if has_critical:
            return "failed", "reject"
        if has_high:
            return "partial", "review"
            
        return "partial", "review"
