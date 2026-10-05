PRAGMA foreign_keys = ON;

ALTER TABLE products ADD COLUMN quantity_mode TEXT NOT NULL DEFAULT 'INTEGER';
ALTER TABLE purchases ADD COLUMN discount_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE purchases ADD COLUMN additional_costs_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE purchases ADD COLUMN subtotal_cents INTEGER NOT NULL DEFAULT 0;
ALTER TABLE purchases ADD COLUMN payment_method TEXT;
ALTER TABLE purchases ADD COLUMN expected_received_at TEXT;

CREATE INDEX IF NOT EXISTS idx_products_active_name ON products(active, name);
CREATE INDEX IF NOT EXISTS idx_purchase_details_product_purchase ON purchase_details(product_id, purchase_id);
CREATE INDEX IF NOT EXISTS idx_lots_product_status_remaining ON lots(product_id, status, quantity_remaining);
CREATE INDEX IF NOT EXISTS idx_purchases_status_received ON purchases(status, received_at);
