CREATE TABLE IF NOT EXISTS changelog_entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  version TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'feature',
  is_breaking INTEGER NOT NULL DEFAULT 0,
  published_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_changelog_date ON changelog_entries(published_at DESC);

INSERT INTO changelog_entries (version, title, description, category) VALUES
('1.16.0', 'SDK Code Generator', 'Generate SDK snippets in 5 languages from the API', 'feature'),
('1.16.0', 'Rate Limit Dashboard', 'View and manage rate limits per tenant', 'feature'),
('1.15.0', 'Recurring Missions', 'Schedule missions with cron expressions', 'feature'),
('1.15.0', 'Tenant Health Scoring', 'AI-powered churn prediction with health scores', 'feature'),
('1.14.0', 'Mission Templates', 'Reusable templates for common mission types', 'feature'),
('1.13.0', 'Usage Metering', 'Track API usage with daily/monthly counters', 'feature'),
('1.12.0', 'Landing Page', 'Public landing page served from Worker', 'improvement'),
('1.10.0', 'Team Members', 'Invite team members with role-based access', 'feature'),
('1.9.0', 'Referral System', 'Earn credits by referring new tenants', 'feature');
