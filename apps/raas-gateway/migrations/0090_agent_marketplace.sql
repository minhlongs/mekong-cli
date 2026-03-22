-- Wave 37.3: AI Agent Marketplace
-- Tables: marketplace_agents, agent_installations, agent_reviews

CREATE TABLE IF NOT EXISTS marketplace_agents (
  id TEXT PRIMARY KEY,
  publisher_id TEXT NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  category TEXT NOT NULL DEFAULT 'general', -- general, coding, writing, analysis, automation
  pricing_type TEXT NOT NULL DEFAULT 'free', -- free, credits, subscription
  price_credits INTEGER DEFAULT 0,
  version TEXT DEFAULT '1.0.0',
  config_schema TEXT, -- JSON schema for agent config
  system_prompt TEXT,
  model_preference TEXT,
  install_count INTEGER DEFAULT 0,
  rating_avg REAL DEFAULT 0,
  rating_count INTEGER DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'draft', -- draft, published, suspended
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);
CREATE INDEX idx_mp_agents_publisher ON marketplace_agents(publisher_id);
CREATE INDEX idx_mp_agents_category ON marketplace_agents(category);
CREATE INDEX idx_mp_agents_status ON marketplace_agents(status);

CREATE TABLE IF NOT EXISTS agent_installations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  config TEXT, -- JSON tenant-specific config
  installed_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_used_at TEXT,
  usage_count INTEGER DEFAULT 0,
  UNIQUE(tenant_id, agent_id)
);
CREATE INDEX idx_installations_tenant ON agent_installations(tenant_id);

CREATE TABLE IF NOT EXISTS agent_reviews (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
  review TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(agent_id, tenant_id)
);
CREATE INDEX idx_agent_reviews_agent ON agent_reviews(agent_id);
