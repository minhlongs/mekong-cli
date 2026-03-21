-- Migration 0017: Add tags column to missions table
ALTER TABLE missions ADD COLUMN tags TEXT DEFAULT '[]';
