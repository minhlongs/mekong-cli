-- Wave 54: Admin Deployment Manager for RaaS Gateway
-- Creates deployments, deployment_checks, and canary_configs tables

CREATE TABLE IF NOT EXISTS deployments (
  id TEXT PRIMARY KEY,
  version TEXT NOT NULL,
  environment TEXT DEFAULT 'production',
  status TEXT DEFAULT 'pending',
  deploy_type TEXT DEFAULT 'full',
  commit_hash TEXT,
  release_notes TEXT,
  deployed_by TEXT,
  started_at TEXT,
  completed_at TEXT,
  rollback_from TEXT,
  canary_percentage INTEGER DEFAULT 0,
  health_check_url TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deployment_checks (
  id TEXT PRIMARY KEY,
  deployment_id TEXT NOT NULL,
  check_type TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  result_json TEXT DEFAULT '{}',
  checked_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS canary_configs (
  id TEXT PRIMARY KEY,
  deployment_id TEXT NOT NULL,
  percentage INTEGER DEFAULT 10,
  duration_minutes INTEGER DEFAULT 30,
  success_threshold REAL DEFAULT 0.99,
  auto_promote INTEGER DEFAULT 0,
  metrics_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for deployments
CREATE INDEX IF NOT EXISTS idx_deployments_environment ON deployments(environment);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON deployments(status);
CREATE INDEX IF NOT EXISTS idx_deployments_version ON deployments(version);

-- Indexes for deployment_checks
CREATE INDEX IF NOT EXISTS idx_deployment_checks_deployment_id ON deployment_checks(deployment_id);
CREATE INDEX IF NOT EXISTS idx_deployment_checks_status ON deployment_checks(status);

-- Indexes for canary_configs
CREATE INDEX IF NOT EXISTS idx_canary_configs_deployment_id ON canary_configs(deployment_id);
