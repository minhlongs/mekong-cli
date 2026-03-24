-- Migration: Create reviews table
-- Created: 2026-03-17
-- Purpose: Customer reviews for menu items with star ratings

-- =====================================================
-- REVIEWS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL,  -- References menu_items.id
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),  -- 1-5 stars
    comment TEXT,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for filtering by menu item
CREATE INDEX idx_reviews_item_id ON reviews(item_id);

-- Index for sorting by date
CREATE INDEX idx_reviews_created_at ON reviews(created_at);

-- Index for rating aggregation
CREATE INDEX idx_reviews_rating ON reviews(rating);

-- =====================================================
-- TRIGGER FOR updated_at
-- =====================================================
CREATE TRIGGER update_reviews_timestamp
AFTER UPDATE ON reviews
BEGIN
    UPDATE reviews SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
