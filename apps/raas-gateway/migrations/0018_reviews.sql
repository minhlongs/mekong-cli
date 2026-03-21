-- Migration 0018: marketplace reviews system
-- Adds per-mission ratings and comments for social proof

CREATE TABLE IF NOT EXISTS reviews (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
  comment TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (mission_id) REFERENCES missions(id),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_reviews_mission ON reviews(mission_id);
