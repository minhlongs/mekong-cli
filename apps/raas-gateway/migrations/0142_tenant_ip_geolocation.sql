-- Wave 55: Tenant IP Geolocation for RaaS Gateway
-- Tables: ip_geolocation_cache, geo_fencing_rules, geo_access_logs

CREATE TABLE IF NOT EXISTS ip_geolocation_cache (
  id TEXT PRIMARY KEY,
  ip_address TEXT NOT NULL,
  country_code TEXT,
  country_name TEXT,
  region TEXT,
  city TEXT,
  latitude REAL,
  longitude REAL,
  isp TEXT,
  cached_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geo_fencing_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_type TEXT DEFAULT 'allow',
  country_codes_json TEXT DEFAULT '[]',
  description TEXT,
  enabled INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS geo_access_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  ip_address TEXT NOT NULL,
  country_code TEXT,
  action TEXT DEFAULT 'allowed',
  rule_id TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ip_geolocation_cache
CREATE UNIQUE INDEX IF NOT EXISTS idx_ip_geolocation_cache_ip ON ip_geolocation_cache(ip_address);
CREATE INDEX IF NOT EXISTS idx_ip_geolocation_cache_country ON ip_geolocation_cache(country_code);

-- Indexes for geo_fencing_rules
CREATE INDEX IF NOT EXISTS idx_geo_fencing_rules_tenant ON geo_fencing_rules(tenant_id);

-- Indexes for geo_access_logs
CREATE INDEX IF NOT EXISTS idx_geo_access_logs_tenant ON geo_access_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_geo_access_logs_ip ON geo_access_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_geo_access_logs_country ON geo_access_logs(country_code);
