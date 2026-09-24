-- ============================================================
-- PostgreSQL Initialization Script
-- Creates the three schemas used by the platform.
-- This runs ONCE when the PostgreSQL container is first started.
-- ============================================================

-- Schema: audit
-- Owned by Agent Service.
-- Contains invoice audit records, line items, discrepancies, and human feedback.
CREATE SCHEMA IF NOT EXISTS audit;

-- Schema: erp
-- Owned by Mock ERP Service.
-- Contains vendors, purchase orders, PO line items, and SKU master data.
CREATE SCHEMA IF NOT EXISTS erp;

-- Schema: langgraph
-- Managed by LangGraph PostgreSQL checkpointer.
-- Contains checkpoint tables for workflow state persistence.
CREATE SCHEMA IF NOT EXISTS langgraph;

-- Grant usage on schemas to the default postgres user
-- (In production, you would create separate service accounts)
GRANT ALL ON SCHEMA audit TO postgres;
GRANT ALL ON SCHEMA erp TO postgres;
GRANT ALL ON SCHEMA langgraph TO postgres;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Schemas created: audit, erp, langgraph';
END
$$;
