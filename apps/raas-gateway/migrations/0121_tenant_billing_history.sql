-- Migration 0121: Tenant Billing History
-- Invoice history, payment records, and monthly statements for tenant billing

CREATE TABLE IF NOT EXISTS billing_invoices (
  id TEXT PRIMARY KEY DEFAULT ('inv_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  invoice_number TEXT NOT NULL UNIQUE,
  amount_cents INTEGER NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'draft', -- draft, sent, paid, overdue, void
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  line_items_json TEXT NOT NULL DEFAULT '[]', -- JSON array of line items
  issued_at TEXT,
  paid_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_billing_invoices_tenant_id ON billing_invoices(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_invoices_number ON billing_invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_billing_invoices_status ON billing_invoices(status);
CREATE INDEX IF NOT EXISTS idx_billing_invoices_tenant_status ON billing_invoices(tenant_id, status);

CREATE TABLE IF NOT EXISTS billing_payments (
  id TEXT PRIMARY KEY DEFAULT ('pay_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  invoice_id TEXT NOT NULL,
  amount_cents INTEGER NOT NULL DEFAULT 0,
  currency TEXT NOT NULL DEFAULT 'USD',
  payment_method TEXT NOT NULL DEFAULT 'card', -- card, bank_transfer, crypto, polar
  provider_ref TEXT, -- external payment provider reference ID
  status TEXT NOT NULL DEFAULT 'success', -- success, failed, refunded
  paid_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (invoice_id) REFERENCES billing_invoices(id)
);
CREATE INDEX IF NOT EXISTS idx_billing_payments_tenant_id ON billing_payments(tenant_id);
CREATE INDEX IF NOT EXISTS idx_billing_payments_invoice_id ON billing_payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_billing_payments_status ON billing_payments(status);

CREATE TABLE IF NOT EXISTS billing_statements (
  id TEXT PRIMARY KEY DEFAULT ('stmt_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  statement_month TEXT NOT NULL, -- format: YYYY-MM
  total_charges_cents INTEGER NOT NULL DEFAULT 0,
  total_payments_cents INTEGER NOT NULL DEFAULT 0,
  balance_cents INTEGER NOT NULL DEFAULT 0,
  generated_at TEXT NOT NULL DEFAULT (datetime('now')),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_billing_statements_tenant_id ON billing_statements(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_billing_statements_tenant_month ON billing_statements(tenant_id, statement_month);
CREATE INDEX IF NOT EXISTS idx_billing_statements_month ON billing_statements(statement_month);
