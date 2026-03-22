-- Migration: Mission Batch Processing
-- Creates tables for batch job tracking and individual batch items

CREATE TABLE IF NOT EXISTS mission_batch_jobs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  batch_name TEXT NOT NULL,
  total_missions INTEGER NOT NULL DEFAULT 0,
  completed_missions INTEGER NOT NULL DEFAULT 0,
  failed_missions INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_batch_jobs_tenant ON mission_batch_jobs(tenant_id);

CREATE TABLE IF NOT EXISTS mission_batch_items (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  batch_id TEXT NOT NULL,
  mission_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_batch_items_batch ON mission_batch_items(batch_id);
