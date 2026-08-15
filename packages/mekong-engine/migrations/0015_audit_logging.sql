-- Audit Logging System Enhancement
-- Adds missing columns to existing audit_logs table from migration 0014
-- Tamper-proof storage for all sensitive operations

-- Add new columns for HTTP request tracking (if not exist)
ALTER TABLE audit_logs ADD COLUMN request_method TEXT;
ALTER TABLE audit_logs ADD COLUMN request_path TEXT;
ALTER TABLE audit_logs ADD COLUMN status_code INTEGER;
ALTER TABLE audit_logs ADD COLUMN resource_type TEXT;

-- Rename 'resource' column to 'resource_id' for consistency
-- (Note: SQLite doesn't support direct rename, so we keep both or use resource for resource_id)

-- Add metadata column for structured data
ALTER TABLE audit_logs ADD COLUMN metadata TEXT;

-- Drop old indexes if exist and recreate with new names
DROP INDEX IF EXISTS idx_audit_logs_tenant;
DROP INDEX IF EXISTS idx_audit_logs_tenant_id;
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id ON audit_logs(tenant_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_request ON audit_logs(request_method, request_path);

-- Trigger to prevent updates (tamper-proof)
-- Note: This works at runtime - D1 may not support triggers in migrations
CREATE TRIGGER IF NOT EXISTS prevent_audit_log_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Audit logs cannot be modified');
END;

-- Trigger to prevent deletes (tamper-proof)
CREATE TRIGGER IF NOT EXISTS prevent_audit_log_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Audit logs cannot be deleted');
END;
