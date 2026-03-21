-- Migration: 0071_ip_allowlist
-- Created: 2026-03-21
-- Description: Full IP allowlist management — per-tenant with CIDR, expiry, labels, and access logs

CREATE TABLE IF NOT EXISTS ip_allowlists (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  ip_address TEXT NOT NULL, -- single IP or CIDR notation (e.g., 192.168.1.0/24)
  label TEXT,               -- human-readable label
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  expires_at TEXT,          -- optional expiry (ISO 8601)
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ip_allowlist_tenant_ip ON ip_allowlists(tenant_id, ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_allowlist_tenant ON ip_allowlists(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ip_allowlist_active ON ip_allowlists(tenant_id, is_active);

CREATE TABLE IF NOT EXISTS ip_access_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  ip_address TEXT NOT NULL,
  action TEXT NOT NULL,     -- allowed, blocked
  endpoint TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ip_access_tenant ON ip_access_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ip_access_created ON ip_access_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_ip_access_action ON ip_access_logs(tenant_id, action);
