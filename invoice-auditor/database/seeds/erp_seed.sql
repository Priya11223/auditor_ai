-- ============================================================
-- ERP Seed Data
-- Populates erp.vendors, erp.sku_master, erp.purchase_orders,
-- and erp.po_line_items with test data for development.
-- ============================================================

-- ============================================================
-- VENDORS
-- ============================================================
INSERT INTO erp.vendors (vendor_id, vendor_name, vendor_code, address, currency, active)
VALUES
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 'ABC Corp', 'VENDOR-001',
     '123 Business Park, Mumbai, India', 'INR', true),
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567802', 'Global Supplies Ltd', 'VENDOR-002',
     '456 Commerce Ave, Delhi, India', 'INR', true),
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567803', 'TechParts GmbH', 'VENDOR-003',
     'Industriestraße 42, Berlin, Germany', 'EUR', true),
    ('a1b2c3d4-e5f6-7890-abcd-ef1234567804', 'Office World Inc', 'VENDOR-004',
     '789 Supply Chain Blvd, Bangalore, India', 'INR', true)
ON CONFLICT (vendor_code) DO NOTHING;


-- ============================================================
-- SKU MASTER
-- ============================================================
INSERT INTO erp.sku_master (sku_id, sku_code, description, category, standard_price, unit_of_measure, active)
VALUES
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567801', 'SKU-001', 'Laptop - Business Grade', 'Electronics', 1000.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567802', 'SKU-002', 'Wireless Mouse', 'Accessories', 25.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567803', 'SKU-003', 'USB-C Docking Station', 'Accessories', 150.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567804', 'SKU-004', 'Office Chair - Ergonomic', 'Furniture', 350.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567805', 'SKU-005', 'Standing Desk', 'Furniture', 600.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567806', 'SKU-006', 'Monitor 27" 4K', 'Electronics', 450.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567807', 'SKU-007', 'Keyboard - Mechanical', 'Accessories', 80.0000, 'EA', true),
    ('b1b2c3d4-e5f6-7890-abcd-ef1234567808', 'SKU-008', 'Printer - Laser', 'Electronics', 300.0000, 'EA', true)
ON CONFLICT (sku_code) DO NOTHING;


-- ============================================================
-- PURCHASE ORDERS
-- ============================================================

-- PO-1001: ABC Corp, 2 line items (normal valid PO)
INSERT INTO erp.purchase_orders (po_id, po_number, vendor_id, po_date, currency, total_amount, status)
VALUES
    ('c1b2c3d4-e5f6-7890-abcd-ef1234567801', 'PO-1001',
     'a1b2c3d4-e5f6-7890-abcd-ef1234567801', '2026-09-01', 'INR', 10500.0000, 'open')
ON CONFLICT (po_number) DO NOTHING;

INSERT INTO erp.po_line_items (id, po_id, line_number, sku_code, description, quantity, unit_price, line_total)
VALUES
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567801', 'c1b2c3d4-e5f6-7890-abcd-ef1234567801',
     1, 'SKU-001', 'Laptop - Business Grade', 10.0000, 1000.0000, 10000.0000),
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567802', 'c1b2c3d4-e5f6-7890-abcd-ef1234567801',
     2, 'SKU-002', 'Wireless Mouse', 20.0000, 25.0000, 500.0000)
ON CONFLICT DO NOTHING;


-- PO-1002: Global Supplies, 3 line items (furniture order)
INSERT INTO erp.purchase_orders (po_id, po_number, vendor_id, po_date, currency, total_amount, status)
VALUES
    ('c1b2c3d4-e5f6-7890-abcd-ef1234567802', 'PO-1002',
     'a1b2c3d4-e5f6-7890-abcd-ef1234567802', '2026-09-05', 'INR', 5100.0000, 'open')
ON CONFLICT (po_number) DO NOTHING;

INSERT INTO erp.po_line_items (id, po_id, line_number, sku_code, description, quantity, unit_price, line_total)
VALUES
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567803', 'c1b2c3d4-e5f6-7890-abcd-ef1234567802',
     1, 'SKU-004', 'Office Chair - Ergonomic', 10.0000, 350.0000, 3500.0000),
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567804', 'c1b2c3d4-e5f6-7890-abcd-ef1234567802',
     2, 'SKU-005', 'Standing Desk', 2.0000, 600.0000, 1200.0000),
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567805', 'c1b2c3d4-e5f6-7890-abcd-ef1234567802',
     3, 'SKU-002', 'Wireless Mouse', 16.0000, 25.0000, 400.0000)
ON CONFLICT DO NOTHING;


-- PO-1003: TechParts GmbH, EUR currency (for multi-currency / German invoice testing)
INSERT INTO erp.purchase_orders (po_id, po_number, vendor_id, po_date, currency, total_amount, status)
VALUES
    ('c1b2c3d4-e5f6-7890-abcd-ef1234567803', 'PO-1003',
     'a1b2c3d4-e5f6-7890-abcd-ef1234567803', '2026-09-10', 'EUR', 4950.0000, 'open')
ON CONFLICT (po_number) DO NOTHING;

INSERT INTO erp.po_line_items (id, po_id, line_number, sku_code, description, quantity, unit_price, line_total)
VALUES
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567806', 'c1b2c3d4-e5f6-7890-abcd-ef1234567803',
     1, 'SKU-003', 'USB-C Docking Station', 15.0000, 150.0000, 2250.0000),
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567807', 'c1b2c3d4-e5f6-7890-abcd-ef1234567803',
     2, 'SKU-006', 'Monitor 27" 4K', 6.0000, 450.0000, 2700.0000)
ON CONFLICT DO NOTHING;


-- PO-1004: Office World, single item (simple PO for basic tests)
INSERT INTO erp.purchase_orders (po_id, po_number, vendor_id, po_date, currency, total_amount, status)
VALUES
    ('c1b2c3d4-e5f6-7890-abcd-ef1234567804', 'PO-1004',
     'a1b2c3d4-e5f6-7890-abcd-ef1234567804', '2026-09-15', 'INR', 2400.0000, 'open')
ON CONFLICT (po_number) DO NOTHING;

INSERT INTO erp.po_line_items (id, po_id, line_number, sku_code, description, quantity, unit_price, line_total)
VALUES
    ('d1b2c3d4-e5f6-7890-abcd-ef1234567808', 'c1b2c3d4-e5f6-7890-abcd-ef1234567804',
     1, 'SKU-008', 'Printer - Laser', 8.0000, 300.0000, 2400.0000)
ON CONFLICT DO NOTHING;
