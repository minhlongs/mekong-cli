-- Migration: Mission Quality Gates
-- Tables for tenant-scoped quality gate definitions and per-mission evaluations

CREATE TABLE IF NOT EXISTS quality_gates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  gate_name TEXT NOT NULL,
  criteria_json TEXT NOT NULL,
  is_blocking INTEGER NOT NULL DEFAULT 1,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_gates_tenant_id ON quality_gates (tenant_id);

CREATE TABLE IF NOT EXISTS gate_evaluations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  gate_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  passed INTEGER NOT NULL,
  details TEXT,
  evaluated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gate_evaluations_tenant_id ON gate_evaluations (tenant_id);
