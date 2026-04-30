-- ═══════════════════════════════════════════════════════════
--  LUNABLOOM NAIL SALON — SUPABASE SQL SCHEMA
--  Copy & paste this entire script into the Supabase SQL Editor
--  (Database → SQL Editor → New Query → Paste → Run)
-- ═══════════════════════════════════════════════════════════

-- ── CUSTOMERS TABLE ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    id               VARCHAR(8)   PRIMARY KEY,
    name             VARCHAR(100) NOT NULL,
    email            VARCHAR(100) NOT NULL UNIQUE,
    contact          VARCHAR(30)  NOT NULL,
    password         VARCHAR(200) NOT NULL,
    date_registered  VARCHAR(20)  NOT NULL
);

-- ── ORDERS TABLE ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id             VARCHAR(20)  PRIMARY KEY,
    customer_name  VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100),
    service        VARCHAR(200) NOT NULL,
    quantity       VARCHAR(5)   DEFAULT '1',
    date           VARCHAR(20)  NOT NULL,
    time           VARCHAR(10)  NOT NULL,
    status         VARCHAR(20)  DEFAULT 'Pending',
    notes          TEXT,
    created_at     VARCHAR(20)
);

-- ── DISABLE ROW LEVEL SECURITY (for simplicity) ──────────────
--  If you want to keep RLS enabled, you'll need to add policies.
--  For a local/dev project this is fine.
ALTER TABLE customers DISABLE ROW LEVEL SECURITY;
ALTER TABLE orders    DISABLE ROW LEVEL SECURITY;

-- ── OPTIONAL: seed a test customer ───────────────────────────
-- INSERT INTO customers (id, name, email, contact, password, date_registered)
-- VALUES ('TEST0001', 'Maria Santos', 'maria@test.com', '09171234567', 'test123', '2024-01-01 10:00');
