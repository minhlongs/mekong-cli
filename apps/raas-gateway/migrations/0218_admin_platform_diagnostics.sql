-- Admin platform diagnostics — individual health checks and aggregated reports
CREATE TABLE IF NOT EXISTS diagnostic_checks (
  id TEXT PRIMARY KEY,
  check_name TEXT NOT NULL,
  check_type TEXT DEFAULT 'health',
  target TEXT,
  status TEXT DEFAULT 'pass',
  response_time_ms INTEGER,
  error_message TEXT,
  checked_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_checks_type ON diagnostic_checks(check_type);

-- Aggregated diagnostic reports grouping multiple checks into a summary
CREATE TABLE IF NOT EXISTS diagnostic_reports (
  id TEXT PRIMARY KEY,
  report_type TEXT DEFAULT 'full',
  total_checks INTEGER DEFAULT 0,
  passed INTEGER DEFAULT 0,
  failed INTEGER DEFAULT 0,
  summary_json TEXT DEFAULT '{}',
  generated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_reports_type ON diagnostic_reports(report_type);
