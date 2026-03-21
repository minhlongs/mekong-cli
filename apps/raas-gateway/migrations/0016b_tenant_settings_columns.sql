-- Add settings columns to tenants table
ALTER TABLE tenants ADD COLUMN webhook_url TEXT;
ALTER TABLE tenants ADD COLUMN notify_email INTEGER DEFAULT 1;
ALTER TABLE tenants ADD COLUMN notify_telegram INTEGER DEFAULT 1;
