-- Migration: 0009_add_mission_result
-- Created: 2026-03-21
-- Description: Add result and metadata columns to missions table

ALTER TABLE missions ADD COLUMN result TEXT;
ALTER TABLE missions ADD COLUMN metadata TEXT DEFAULT '{}';
