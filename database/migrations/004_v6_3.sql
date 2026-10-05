PRAGMA foreign_keys = ON;

-- V6.3: conserva el precio de venta que el usuario decide al registrar una compra.
-- Si la compra queda pendiente, el precio se aplica cuando la mercancía se recibe.
ALTER TABLE purchase_details ADD COLUMN desired_price_cents INTEGER;
