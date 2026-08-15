CREATE TABLE IF NOT EXISTS skill_profiles (
  id TEXT PRIMARY KEY,
  stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  skills JSON NOT NULL DEFAULT '[]',
  industries JSON NOT NULL DEFAULT '[]',
  availability TEXT DEFAULT 'available' CHECK (availability IN ('available','busy','unavailable')),
  hourly_rate_usd REAL,
  bio TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_skill_stakeholder ON skill_profiles(stakeholder_id);

CREATE TABLE IF NOT EXISTS match_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  requester_id TEXT NOT NULL REFERENCES stakeholders(id),
  request_type TEXT NOT NULL CHECK (request_type IN ('expert_needed','cofounder_needed','mentor_needed','vc_intro')),
  skills_needed JSON NOT NULL DEFAULT '[]',
  industry TEXT,
  description TEXT,
  budget_usd REAL,
  status TEXT DEFAULT 'open' CHECK (status IN ('open','matched','closed','expired')),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS matches (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL REFERENCES match_requests(id),
  matched_stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id),
  match_score REAL NOT NULL DEFAULT 0,
  match_reasons JSON DEFAULT '[]',
  status TEXT DEFAULT 'proposed' CHECK (status IN ('proposed','accepted','rejected','completed')),
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
