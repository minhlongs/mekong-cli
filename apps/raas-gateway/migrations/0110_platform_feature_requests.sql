-- Migration 0110: Platform Feature Requests
-- Tables: feature_requests, feature_request_votes, feature_request_comments

CREATE TABLE IF NOT EXISTS feature_requests (
  id TEXT PRIMARY KEY DEFAULT ('fr_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'general', -- general, api, dashboard, billing, integrations, security
  status TEXT NOT NULL DEFAULT 'submitted', -- submitted, under_review, planned, in_progress, completed, declined
  priority TEXT NOT NULL DEFAULT 'medium', -- low, medium, high, critical
  vote_count INTEGER NOT NULL DEFAULT 0,
  comment_count INTEGER NOT NULL DEFAULT 0,
  admin_response TEXT,
  planned_version TEXT,
  completed_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fr_tenant ON feature_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fr_status ON feature_requests(status);
CREATE INDEX IF NOT EXISTS idx_fr_votes ON feature_requests(vote_count DESC);

CREATE TABLE IF NOT EXISTS feature_request_votes (
  id TEXT PRIMARY KEY DEFAULT ('frv_' || lower(hex(randomblob(8)))),
  feature_request_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_frv_unique ON feature_request_votes(feature_request_id, tenant_id);

CREATE TABLE IF NOT EXISTS feature_request_comments (
  id TEXT PRIMARY KEY DEFAULT ('frc_' || lower(hex(randomblob(8)))),
  feature_request_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  content TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_frc_request ON feature_request_comments(feature_request_id);
