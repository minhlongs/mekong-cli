-- Platform Compliance Audit — SOC2/compliance checks and results tracking

CREATE TABLE IF NOT EXISTS compliance_checks (
  id          TEXT PRIMARY KEY,
  check_name  TEXT NOT NULL,
  category    TEXT NOT NULL,
  standard    TEXT NOT NULL DEFAULT 'SOC2',
  severity    TEXT NOT NULL DEFAULT 'medium',
  check_query TEXT NOT NULL,
  is_active   INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_results (
  id           TEXT PRIMARY KEY,
  check_id     TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'pass',
  details_json TEXT NOT NULL DEFAULT '{}',
  checked_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_category  ON compliance_checks (category);
CREATE INDEX IF NOT EXISTS idx_compliance_results_check_id ON compliance_results (check_id);
CREATE INDEX IF NOT EXISTS idx_compliance_results_status   ON compliance_results (status);
