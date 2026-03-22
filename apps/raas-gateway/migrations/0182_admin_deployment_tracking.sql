-- Migration: Admin Deployment Tracking
CREATE TABLE IF NOT EXISTS deployments (
  id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  environment TEXT NOT NULL DEFAULT 'production',
  deploy_type TEXT NOT NULL DEFAULT 'full',
  status TEXT NOT NULL DEFAULT 'pending',
  deployed_by TEXT,
  commit_hash TEXT,
  changelog TEXT,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_deployments_env ON deployments(environment);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);

CREATE TABLE IF NOT EXISTS deployment_rollbacks (
  id TEXT PRIMARY KEY,
  deployment_id TEXT NOT NULL,
  rollback_to_version TEXT NOT NULL,
  reason TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  initiated_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_deployment_rollbacks_deploy ON deployment_rollbacks(deployment_id);
