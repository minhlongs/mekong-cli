-- Sales leads
CREATE TABLE IF NOT EXISTS sales_leads (
  id TEXT PRIMARY KEY,
  company_name TEXT NOT NULL,
  contact_name TEXT,
  contact_email TEXT,
  stage TEXT DEFAULT 'prospect' CHECK(stage IN ('prospect','qualified','demo','proposal','negotiation','closed_won','closed_lost')),
  source TEXT DEFAULT 'inbound',
  score INTEGER DEFAULT 0,
  estimated_arr REAL DEFAULT 0,
  notes TEXT,
  assigned_to TEXT,
  next_action TEXT,
  next_action_date TEXT,
  converted_tenant_id TEXT,
  lost_reason TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Sales activities log
CREATE TABLE IF NOT EXISTS sales_activities (
  id TEXT PRIMARY KEY,
  lead_id TEXT NOT NULL REFERENCES sales_leads(id),
  activity_type TEXT NOT NULL CHECK(activity_type IN ('call','email','demo','meeting','note','stage_change')),
  description TEXT,
  outcome TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sales_leads_stage ON sales_leads(stage);
CREATE INDEX IF NOT EXISTS idx_sales_leads_score ON sales_leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_sales_activities_lead ON sales_activities(lead_id);
