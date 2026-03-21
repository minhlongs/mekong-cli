-- Migration: 0031_api_key_permissions
-- Created: 2026-03-21
-- Description: Add scope, expires_at, description columns to api_keys table

-- Add scope column (read < write < admin hierarchy)
-- 'read'  = GET endpoints only
-- 'write' = GET + POST + PUT + DELETE (default, backward-compatible)
-- 'admin' = all endpoints including admin routes
ALTER TABLE api_keys ADD COLUMN scope TEXT DEFAULT 'write';

-- Add optional expiry timestamp (ISO 8601)
ALTER TABLE api_keys ADD COLUMN expires_at TEXT;

-- Add human-readable description
ALTER TABLE api_keys ADD COLUMN description TEXT;
