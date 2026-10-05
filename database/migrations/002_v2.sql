PRAGMA foreign_keys = ON;

-- V2: metadatos de producto y recepción. Las fechas de vencimiento siguen perteneciendo a LOTES.
ALTER TABLE products ADD COLUMN normalized_name TEXT;
ALTER TABLE products ADD COLUMN unit_name TEXT NOT NULL DEFAULT 'unidad';
ALTER TABLE purchases ADD COLUMN received_at TEXT;
ALTER TABLE lots ADD COLUMN expiry_updated_at TEXT;

CREATE INDEX IF NOT EXISTS idx_sales_sold_at_status ON sales(sold_at, status);
CREATE INDEX IF NOT EXISTS idx_sale_details_product ON sale_details(product_id, sale_id);
CREATE INDEX IF NOT EXISTS idx_purchases_purchased_at_status ON purchases(purchased_at, status);
CREATE INDEX IF NOT EXISTS idx_lots_product_remaining_expiry ON lots(product_id, quantity_remaining, expiry_date, status);
CREATE INDEX IF NOT EXISTS idx_receivables_customer_status ON receivables(customer_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_paid_at_status ON payments(paid_at, status);
CREATE INDEX IF NOT EXISTS idx_movements_created_product ON inventory_movements(created_at, product_id);
