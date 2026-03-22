CREATE TABLE IF NOT EXISTS api_mock_endpoints (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, mock_path TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'GET', response_status INTEGER DEFAULT 200,
  response_body_json TEXT DEFAULT '{}', response_headers_json TEXT DEFAULT '{}',
  delay_ms INTEGER DEFAULT 0, is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_mock_endpoints_tenant ON api_mock_endpoints(tenant_id);

CREATE TABLE IF NOT EXISTS api_mock_requests (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, mock_id TEXT NOT NULL,
  request_method TEXT NOT NULL, request_path TEXT NOT NULL,
  request_headers_json TEXT DEFAULT '{}', request_body TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_api_mock_requests_tenant ON api_mock_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_mock_requests_mock ON api_mock_requests(mock_id);
