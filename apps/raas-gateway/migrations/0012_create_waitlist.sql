-- Migration: 0012_create_waitlist

CREATE TABLE IF NOT EXISTS waitlist (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  source TEXT DEFAULT 'landing',
  created_at TEXT DEFAULT (datetime('now'))
);
