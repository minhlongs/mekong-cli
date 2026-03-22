-- Wave 54: API Documentation Generator for RaaS Gateway
-- Tables: api_doc_endpoints, api_doc_versions, api_doc_examples

CREATE TABLE IF NOT EXISTS api_doc_endpoints (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  method TEXT NOT NULL,
  summary TEXT,
  description TEXT,
  tag TEXT DEFAULT 'General',
  request_schema_json TEXT DEFAULT '{}',
  response_schema_json TEXT DEFAULT '{}',
  example_request_json TEXT DEFAULT '{}',
  example_response_json TEXT DEFAULT '{}',
  auth_required INTEGER DEFAULT 1,
  deprecated INTEGER DEFAULT 0,
  version TEXT DEFAULT 'v1',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_doc_versions (
  id TEXT PRIMARY KEY,
  version TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft',
  published_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_doc_examples (
  id TEXT PRIMARY KEY,
  endpoint_id TEXT NOT NULL,
  language TEXT DEFAULT 'curl',
  code TEXT NOT NULL,
  description TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for api_doc_endpoints
CREATE INDEX IF NOT EXISTS idx_api_doc_endpoints_path ON api_doc_endpoints(path);
CREATE INDEX IF NOT EXISTS idx_api_doc_endpoints_method ON api_doc_endpoints(method);
CREATE INDEX IF NOT EXISTS idx_api_doc_endpoints_tag ON api_doc_endpoints(tag);
CREATE INDEX IF NOT EXISTS idx_api_doc_endpoints_version ON api_doc_endpoints(version);
CREATE UNIQUE INDEX IF NOT EXISTS idx_api_doc_endpoints_path_method_version ON api_doc_endpoints(path, method, version);

-- Index for api_doc_examples
CREATE INDEX IF NOT EXISTS idx_api_doc_examples_endpoint_id ON api_doc_examples(endpoint_id);
