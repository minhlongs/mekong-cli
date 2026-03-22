-- Wave 42: Tenant Invoicing — auto-generated invoices with line items and payment tracking

CREATE TABLE IF NOT EXISTS invoices (
  id TEXT PRIMARY KEY DEFAULT ('inv_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  invoice_number TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'draft', -- draft, sent, paid, overdue, cancelled, refunded
  currency TEXT NOT NULL DEFAULT 'USD',
  subtotal INTEGER NOT NULL DEFAULT 0, -- cents
  tax_amount INTEGER NOT NULL DEFAULT 0,
  discount_amount INTEGER NOT NULL DEFAULT 0,
  total INTEGER NOT NULL DEFAULT 0, -- cents
  billing_period_start TEXT,
  billing_period_end TEXT,
  due_date TEXT,
  paid_at TEXT,
  payment_method TEXT,
  payment_reference TEXT,
  notes TEXT,
  metadata TEXT DEFAULT '{}', -- JSON
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_inv_tenant ON invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_inv_status ON invoices(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_inv_number ON invoices(invoice_number);

CREATE TABLE IF NOT EXISTS invoice_line_items (
  id TEXT PRIMARY KEY DEFAULT ('ili_' || lower(hex(randomblob(8)))),
  invoice_id TEXT NOT NULL,
  description TEXT NOT NULL,
  quantity REAL NOT NULL DEFAULT 1,
  unit_price INTEGER NOT NULL DEFAULT 0, -- cents
  amount INTEGER NOT NULL DEFAULT 0, -- cents
  item_type TEXT NOT NULL DEFAULT 'usage', -- usage, subscription, credit, adjustment, tax
  reference_id TEXT, -- mission_id, subscription_id, etc.
  metadata TEXT DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ili_invoice ON invoice_line_items(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ili_type ON invoice_line_items(item_type);
