-- Platform feature gating: tier-based feature access with per-tenant overrides
CREATE TABLE IF NOT EXISTS feature_gates (
  id TEXT PRIMARY KEY,
  feature_key TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT,
  allowed_tiers TEXT DEFAULT 'pro,enterprise',
  is_enabled INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Per-tenant overrides: enable/disable a gate for a specific tenant regardless of tier
CREATE TABLE IF NOT EXISTS feature_gate_overrides (
  id TEXT PRIMARY KEY,
  gate_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  is_enabled INTEGER NOT NULL,
  reason TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feature_gates_key ON feature_gates(feature_key);
CREATE INDEX IF NOT EXISTS idx_feature_gate_overrides_gate_id ON feature_gate_overrides(gate_id);
CREATE INDEX IF NOT EXISTS idx_feature_gate_overrides_tenant_id ON feature_gate_overrides(tenant_id);
