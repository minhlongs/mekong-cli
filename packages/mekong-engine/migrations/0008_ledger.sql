-- Double-entry credit ledger — auditable, immutable
CREATE TABLE IF NOT EXISTS ledger_accounts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  owner_id TEXT, -- stakeholder_id or 'platform' or 'treasury'
  code TEXT NOT NULL, -- 'credits:customer:xxx' or 'revenue:platform'
  account_type TEXT NOT NULL CHECK (account_type IN ('asset', 'liability', 'equity', 'revenue', 'expense')),
  balance INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(tenant_id, code)
);

CREATE TABLE IF NOT EXISTS journal_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  description TEXT NOT NULL,
  entry_type TEXT NOT NULL, -- 'topup', 'consume', 'revenue_share', 'refund', 'qf_match'
  idempotency_key TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'posted' CHECK (status IN ('pending', 'posted', 'reversed')),
  posted_at TEXT NOT NULL DEFAULT (datetime('now')),
  metadata JSON DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS transaction_lines (
  id TEXT PRIMARY KEY,
  journal_entry_id TEXT NOT NULL REFERENCES journal_entries(id),
  account_id TEXT NOT NULL REFERENCES ledger_accounts(id),
  amount INTEGER NOT NULL,
  direction INTEGER NOT NULL CHECK (direction IN (1, -1)), -- 1=debit, -1=credit
  running_balance INTEGER
);
CREATE INDEX IF NOT EXISTS idx_txn_journal ON transaction_lines(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_txn_account ON transaction_lines(account_id);
