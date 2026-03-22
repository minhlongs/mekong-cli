-- Migration: Admin platform usage report tables
-- Stores periodic platform-wide usage snapshots and their sectioned breakdown

CREATE TABLE IF NOT EXISTS platform_usage_reports (
  id TEXT PRIMARY KEY,
  report_name TEXT NOT NULL,
  period TEXT NOT NULL,
  total_tenants INTEGER DEFAULT 0,
  total_missions INTEGER DEFAULT 0,
  total_api_calls INTEGER DEFAULT 0,
  revenue REAL DEFAULT 0,
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_usage_reports_period ON platform_usage_reports(period);

CREATE TABLE IF NOT EXISTS platform_usage_report_sections (
  id TEXT PRIMARY KEY,
  report_id TEXT NOT NULL,
  section_name TEXT NOT NULL,
  section_data TEXT NOT NULL,
  display_order INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_usage_report_sections_report ON platform_usage_report_sections(report_id);
