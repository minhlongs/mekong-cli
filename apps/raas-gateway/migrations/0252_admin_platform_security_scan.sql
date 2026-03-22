-- Migration: Admin Platform Security Scan tables
-- Tracks security scans and their findings across the platform

CREATE TABLE IF NOT EXISTS platform_security_scans (
  id TEXT PRIMARY KEY,
  scan_type TEXT NOT NULL,
  target TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  findings_count INTEGER DEFAULT 0,
  severity_high INTEGER DEFAULT 0,
  severity_medium INTEGER DEFAULT 0,
  severity_low INTEGER DEFAULT 0,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_security_scans_type ON platform_security_scans(scan_type);

CREATE TABLE IF NOT EXISTS platform_security_findings (
  id TEXT PRIMARY KEY,
  scan_id TEXT NOT NULL,
  finding_type TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'medium',
  description TEXT NOT NULL,
  remediation TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_security_findings_scan ON platform_security_findings(scan_id);
