-- Migration: 0001_create_leads_and_activities.sql
-- Created: 2026-03-20
-- Description: Initial CRM schema for leads and activities tracking

-- Leads table: Core CRM entity for tracking potential customers
CREATE TABLE IF NOT EXISTS leads (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  company_name TEXT NOT NULL,
  contact_name TEXT,
  email TEXT,
  phone TEXT,
  stage TEXT CHECK (stage IN ('new', 'contacted', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost')) DEFAULT 'new',
  estimated_value INTEGER DEFAULT 0,
  probability INTEGER DEFAULT 0 CHECK (probability >= 0 AND probability <= 100),
  last_contact_date TEXT,
  next_followup_date TEXT,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Activities table: Track all interactions with leads
CREATE TABLE IF NOT EXISTS activities (
  id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
  lead_id TEXT NOT NULL,
  activity_type TEXT CHECK (activity_type IN ('call', 'email', 'meeting', 'note', 'task', 'other')) DEFAULT 'note',
  description TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_stage ON leads(stage);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_next_followup ON leads(next_followup_date) WHERE next_followup_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activities_lead_id ON activities(lead_id);

-- Trigger: Update updated_at timestamp on leads
CREATE TRIGGER IF NOT EXISTS update_leads_updated_at
AFTER UPDATE ON leads
BEGIN
  UPDATE leads SET updated_at = datetime('now') WHERE id = NEW.id;
END;
