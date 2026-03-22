-- Service registry: track internal/external services with health and dependency graph
CREATE TABLE IF NOT EXISTS service_registry_entries (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL,
  service_url TEXT NOT NULL,
  health_endpoint TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  version TEXT,
  last_health_check TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_service_registry_status ON service_registry_entries(status);

-- Dependency edges between registered services
CREATE TABLE IF NOT EXISTS service_registry_dependencies (
  id TEXT PRIMARY KEY,
  service_id TEXT NOT NULL,
  depends_on_service_id TEXT NOT NULL,
  dependency_type TEXT NOT NULL DEFAULT 'required',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_service_registry_deps_service ON service_registry_dependencies(service_id);
