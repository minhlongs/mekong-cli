-- ═══════════════════════════════════════════════════════════════
-- BINH PHÁP VC STUDIO — Governance Schema
-- Multi-stakeholder: VC ↔ Expert ↔ Founder ↔ Developer ↔ Customer
-- Tam Giác Ngược: Community (top) → Builders (mid) → Owner (base)
-- ═══════════════════════════════════════════════════════════════

-- Stakeholder registry (mở rộng tenant concept)
CREATE TABLE IF NOT EXISTS stakeholders (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  email TEXT,
  role TEXT NOT NULL DEFAULT 'community' CHECK (role IN (
    'owner', 'admin', 'operator', 'vc_partner', 'founder',
    'expert', 'developer', 'customer', 'community'
  )),
  -- Governance level: 1=owner (ít quyền nhất daily ops) → 6=community (nhiều nhất)
  governance_level INTEGER NOT NULL DEFAULT 6,
  voice_credits_monthly INTEGER NOT NULL DEFAULT 10,
  reputation_score INTEGER NOT NULL DEFAULT 0,
  metadata JSON DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_stakeholder_tenant ON stakeholders(tenant_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_role ON stakeholders(role);

-- Proposals (quadratic voting targets)
CREATE TABLE IF NOT EXISTS proposals (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  author_id TEXT NOT NULL REFERENCES stakeholders(id),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  proposal_type TEXT NOT NULL DEFAULT 'feature' CHECK (proposal_type IN (
    'feature', 'strategic', 'constitutional', 'treasury', 'equity'
  )),
  voting_mechanism TEXT NOT NULL DEFAULT 'quadratic' CHECK (voting_mechanism IN (
    'quadratic', 'simple_majority', 'supermajority'
  )),
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
    'draft', 'discussion', 'voting', 'approved', 'rejected', 'implemented'
  )),
  quorum_pct REAL NOT NULL DEFAULT 0.10,
  voice_credits_pool INTEGER NOT NULL DEFAULT 0,
  voting_starts_at TEXT,
  voting_ends_at TEXT,
  result_summary JSON,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_proposal_tenant ON proposals(tenant_id);
CREATE INDEX IF NOT EXISTS idx_proposal_status ON proposals(status);

-- Votes (quadratic: cost of n votes = n²)
CREATE TABLE IF NOT EXISTS votes (
  id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
  stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id),
  voice_credits_spent INTEGER NOT NULL,
  votes_cast REAL NOT NULL, -- sqrt(credits_spent)
  direction TEXT NOT NULL DEFAULT 'for' CHECK (direction IN ('for', 'against', 'abstain')),
  cast_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(proposal_id, stakeholder_id)
);
CREATE INDEX IF NOT EXISTS idx_vote_proposal ON votes(proposal_id);

-- Reputation events (track contributions)
CREATE TABLE IF NOT EXISTS reputation_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id),
  tenant_id TEXT NOT NULL,
  dimension TEXT NOT NULL DEFAULT 'general' CHECK (dimension IN (
    'code', 'mentorship', 'governance', 'expertise', 'community', 'general'
  )),
  points_delta INTEGER NOT NULL,
  reason TEXT NOT NULL,
  evidence_ref TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_rep_stakeholder ON reputation_events(stakeholder_id);

-- Ngũ Sự scores (per portfolio company)
CREATE TABLE IF NOT EXISTS ngu_su_scores (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  entity_name TEXT NOT NULL,
  dao_score REAL NOT NULL DEFAULT 0 CHECK (dao_score BETWEEN 0 AND 5),
  thien_score REAL NOT NULL DEFAULT 0 CHECK (thien_score BETWEEN 0 AND 5),
  dia_score REAL NOT NULL DEFAULT 0 CHECK (dia_score BETWEEN 0 AND 5),
  tuong_score REAL NOT NULL DEFAULT 0 CHECK (tuong_score BETWEEN 0 AND 5),
  phap_score REAL NOT NULL DEFAULT 0 CHECK (phap_score BETWEEN 0 AND 5),
  overall_score REAL GENERATED ALWAYS AS (
    (dao_score + thien_score + dia_score + tuong_score + phap_score) / 5.0
  ) STORED,
  terrain TEXT DEFAULT 'unknown' CHECK (terrain IN (
    'tan_dia', 'khinh_dia', 'tranh_dia', 'giao_dia',
    'trung_dia', 'vi_dia', 'tu_dia', 'unknown'
  )),
  scored_at TEXT NOT NULL DEFAULT (datetime('now')),
  notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_ngusu_tenant ON ngu_su_scores(tenant_id);

-- Community treasury (quadratic funding matching pool)
CREATE TABLE IF NOT EXISTS treasury (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  balance INTEGER NOT NULL DEFAULT 0,
  total_in INTEGER NOT NULL DEFAULT 0,
  total_out INTEGER NOT NULL DEFAULT 0,
  last_updated TEXT NOT NULL DEFAULT (datetime('now'))
);
