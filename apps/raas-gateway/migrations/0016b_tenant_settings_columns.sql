-- Add settings columns to tenants table (idempotent — columns may already exist)
-- D1 does not support ALTER TABLE ... IF NOT EXISTS, so we use a CREATE TABLE trick
-- Columns: webhook_url, notify_email, notify_telegram were added in earlier deploy
SELECT 1;
