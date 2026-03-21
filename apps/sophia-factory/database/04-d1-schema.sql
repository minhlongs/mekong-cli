-- Sophia AI Factory - Cloudflare D1 Schema (SQLite)
-- Run: wrangler d1 execute sophia-factory-db --file=database/04-d1-schema.sql

-- Organizations (Agencies)
CREATE TABLE IF NOT EXISTS organizations (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'starter',
  proposals_remaining INTEGER DEFAULT 10,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Users (managed by Supabase Auth - this is just a reference table)
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  org_id TEXT REFERENCES organizations(id),
  role TEXT DEFAULT 'member',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Brand Voices
CREATE TABLE IF NOT EXISTS brand_voices (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  org_id TEXT REFERENCES organizations(id) UNIQUE,
  training_docs_count INTEGER DEFAULT 0,
  model_status TEXT DEFAULT 'not_trained',
  voice_characteristics TEXT,  -- JSON string in SQLite
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Proposals
CREATE TABLE IF NOT EXISTS proposals (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  org_id TEXT REFERENCES organizations(id),
  title TEXT NOT NULL,
  client_name TEXT,
  status TEXT DEFAULT 'draft',
  content TEXT,  -- JSON string in SQLite
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Templates
CREATE TABLE IF NOT EXISTS templates (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  name TEXT NOT NULL,
  category TEXT,
  sections TEXT,  -- JSON string in SQLite
  is_public INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Training Documents
CREATE TABLE IF NOT EXISTS training_documents (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  org_id TEXT REFERENCES organizations(id),
  file_url TEXT NOT NULL,
  file_name TEXT,
  file_type TEXT,
  processed INTEGER DEFAULT 0,
  content_text TEXT,
  embedding TEXT,  -- JSON array string for SQLite (D1 doesn't support vector type)
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_proposals_org_id ON proposals(org_id);
CREATE INDEX IF NOT EXISTS idx_training_docs_org_id ON training_documents(org_id);
CREATE INDEX IF NOT EXISTS idx_brand_voices_org_id ON brand_voices(org_id);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
