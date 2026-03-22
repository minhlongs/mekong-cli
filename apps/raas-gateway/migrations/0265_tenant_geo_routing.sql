-- Migration: tenant geo routing rules and analytics
-- Stores per-tenant geo-based routing rules and request analytics

CREATE TABLE IF NOT EXISTS geo_routing_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  source_region TEXT NOT NULL,
  target_endpoint TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geo_routing_rules_tenant ON geo_routing_rules(tenant_id);

CREATE TABLE IF NOT EXISTS geo_routing_analytics (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  source_country TEXT,
  requests_count INTEGER DEFAULT 0,
  avg_latency_ms REAL,
  recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_geo_routing_analytics_tenant ON geo_routing_analytics(tenant_id);
