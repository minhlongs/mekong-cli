-- Wave 52: API Contract Testing for RaaS Gateway
-- Creates api_contracts, contract_validations, and breaking_changes tables

CREATE TABLE IF NOT EXISTS api_contracts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  api_path TEXT NOT NULL,
  method TEXT DEFAULT 'GET',
  version TEXT DEFAULT '1.0.0',
  schema_json TEXT NOT NULL DEFAULT '{}',
  request_schema_json TEXT DEFAULT '{}',
  response_schema_json TEXT DEFAULT '{}',
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contract_validations (
  id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  validation_status TEXT DEFAULT 'pending',
  errors_json TEXT DEFAULT '[]',
  warnings_json TEXT DEFAULT '[]',
  validated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  validated_by TEXT
);

CREATE TABLE IF NOT EXISTS breaking_changes (
  id TEXT PRIMARY KEY,
  contract_id TEXT NOT NULL,
  change_type TEXT NOT NULL,
  description TEXT NOT NULL,
  old_schema TEXT,
  new_schema TEXT,
  severity TEXT DEFAULT 'major',
  acknowledged INTEGER DEFAULT 0,
  detected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_contract_validations_contract_id ON contract_validations(contract_id);
CREATE INDEX IF NOT EXISTS idx_contract_validations_status ON contract_validations(validation_status);
CREATE INDEX IF NOT EXISTS idx_api_contracts_api_path ON api_contracts(api_path);
CREATE INDEX IF NOT EXISTS idx_breaking_changes_contract_id ON breaking_changes(contract_id);
CREATE INDEX IF NOT EXISTS idx_breaking_changes_severity ON breaking_changes(severity);
