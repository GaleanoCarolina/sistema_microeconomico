PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS categories (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE,
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS suppliers (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE,
 phone TEXT, address TEXT, default_lead_days INTEGER DEFAULT 4,
 active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE,
 category_id INTEGER REFERENCES categories(id),
 usual_supplier_id INTEGER REFERENCES suppliers(id),
 stock_qty REAL NOT NULL DEFAULT 0 CHECK(stock_qty >= 0),
 cpp_cents INTEGER NOT NULL DEFAULT 0 CHECK(cpp_cents >= 0),
 price_cents INTEGER NOT NULL DEFAULT 0 CHECK(price_cents >= 0),
 markup_pct TEXT NOT NULL DEFAULT '25',
 min_stock REAL NOT NULL DEFAULT 5,
 safety_stock REAL NOT NULL DEFAULT 3,
 expires INTEGER NOT NULL DEFAULT 0,
 favorite INTEGER NOT NULL DEFAULT 0,
 active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS customers (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL,
 phone TEXT, address TEXT, notes TEXT,
 credit_limit_cents INTEGER NOT NULL DEFAULT 0,
 active INTEGER NOT NULL DEFAULT 1,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);
CREATE TABLE IF NOT EXISTS purchases (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 supplier_id INTEGER REFERENCES suppliers(id),
 total_cents INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'RECEIVED',
 purchased_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 notes TEXT
);
CREATE TABLE IF NOT EXISTS purchase_details (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 purchase_id INTEGER NOT NULL REFERENCES purchases(id),
 product_id INTEGER NOT NULL REFERENCES products(id),
 quantity REAL NOT NULL CHECK(quantity > 0),
 unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0),
 subtotal_cents INTEGER NOT NULL CHECK(subtotal_cents >= 0),
 expiry_date TEXT
);
CREATE TABLE IF NOT EXISTS lots (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 purchase_detail_id INTEGER REFERENCES purchase_details(id),
 quantity_initial REAL NOT NULL CHECK(quantity_initial >= 0),
 quantity_remaining REAL NOT NULL CHECK(quantity_remaining >= 0),
 unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0),
 expiry_date TEXT,
 received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 status TEXT NOT NULL DEFAULT 'ACTIVE'
);
CREATE INDEX IF NOT EXISTS idx_lots_fefo ON lots(product_id, expiry_date, received_at);
CREATE TABLE IF NOT EXISTS sales (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 customer_id INTEGER REFERENCES customers(id),
 total_cents INTEGER NOT NULL DEFAULT 0,
 cost_cents INTEGER NOT NULL DEFAULT 0,
 gross_profit_cents INTEGER NOT NULL DEFAULT 0,
 paid_cents INTEGER NOT NULL DEFAULT 0,
 credit_cents INTEGER NOT NULL DEFAULT 0,
 payment_method TEXT NOT NULL DEFAULT 'CASH',
 status TEXT NOT NULL DEFAULT 'COMPLETED',
 sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 notes TEXT
);
CREATE TABLE IF NOT EXISTS sale_details (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 sale_id INTEGER NOT NULL REFERENCES sales(id),
 product_id INTEGER NOT NULL REFERENCES products(id),
 quantity REAL NOT NULL CHECK(quantity > 0),
 unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents >= 0),
 unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0),
 subtotal_cents INTEGER NOT NULL CHECK(subtotal_cents >= 0),
 cost_total_cents INTEGER NOT NULL CHECK(cost_total_cents >= 0)
);
CREATE TABLE IF NOT EXISTS sale_lot_allocations (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 sale_detail_id INTEGER NOT NULL REFERENCES sale_details(id),
 lot_id INTEGER NOT NULL REFERENCES lots(id),
 quantity REAL NOT NULL CHECK(quantity > 0),
 unit_cost_cents INTEGER NOT NULL CHECK(unit_cost_cents >= 0)
);
CREATE TABLE IF NOT EXISTS receivables (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 sale_id INTEGER NOT NULL UNIQUE REFERENCES sales(id),
 customer_id INTEGER NOT NULL REFERENCES customers(id),
 original_cents INTEGER NOT NULL CHECK(original_cents >= 0),
 balance_cents INTEGER NOT NULL CHECK(balance_cents >= 0),
 status TEXT NOT NULL DEFAULT 'PENDING',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 paid_at TEXT
);
CREATE TABLE IF NOT EXISTS payments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 receivable_id INTEGER NOT NULL REFERENCES receivables(id),
 customer_id INTEGER NOT NULL REFERENCES customers(id),
 amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
 status TEXT NOT NULL DEFAULT 'VALID',
 paid_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 notes TEXT
);
CREATE TABLE IF NOT EXISTS inventory_movements (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 lot_id INTEGER REFERENCES lots(id),
 movement_type TEXT NOT NULL,
 quantity REAL NOT NULL,
 unit_cost_cents INTEGER NOT NULL DEFAULT 0,
 reference_type TEXT,
 reference_id INTEGER,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 notes TEXT
);
CREATE TABLE IF NOT EXISTS price_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 old_price_cents INTEGER NOT NULL,
 new_price_cents INTEGER NOT NULL,
 reason TEXT,
 changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cost_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 old_cpp_cents INTEGER NOT NULL,
 new_cpp_cents INTEGER NOT NULL,
 reason TEXT,
 changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 event_type TEXT NOT NULL,
 entity_type TEXT,
 entity_id INTEGER,
 description TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS settings (
 key TEXT PRIMARY KEY,
 value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stockout_days (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER NOT NULL REFERENCES products(id),
 day TEXT NOT NULL,
 UNIQUE(product_id, day)
);
