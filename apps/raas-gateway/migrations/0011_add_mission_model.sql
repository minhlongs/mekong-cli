-- Migration: 0011_add_mission_model
-- Add model + is_public fields to missions

ALTER TABLE missions ADD COLUMN model TEXT DEFAULT 'auto';
ALTER TABLE missions ADD COLUMN is_public INTEGER DEFAULT 0;
