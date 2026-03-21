-- Migration: 0033_mission_templates
-- Created: 2026-03-21
-- Description: Mission Templates Library for marketplace listing and tenant-owned templates

CREATE TABLE IF NOT EXISTS mission_templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT,
  category TEXT NOT NULL,
  goal_template TEXT NOT NULL,
  default_model TEXT DEFAULT 'auto',
  estimated_credits INTEGER DEFAULT 1,
  is_public INTEGER DEFAULT 0,
  creator_tenant_id TEXT,
  usage_count INTEGER DEFAULT 0,
  rating_sum INTEGER DEFAULT 0,
  rating_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (creator_tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_template_category ON mission_templates(category);
CREATE INDEX IF NOT EXISTS idx_template_public ON mission_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_template_slug ON mission_templates(slug);

-- Seed 5 built-in public templates
INSERT OR IGNORE INTO mission_templates (id, name, slug, description, category, goal_template, default_model, estimated_credits, is_public) VALUES
  ('tpl_seo_audit', 'SEO Audit', 'seo-audit', 'Analyze a URL for SEO issues and recommendations', 'seo-audit', 'Analyze {url} for SEO issues and provide recommendations', 'auto', 3, 1),
  ('tpl_blog_post', 'Blog Post Writer', 'blog-post-writer', 'Generate a blog post on any topic', 'content-generation', 'Write a {wordCount}-word blog post about {topic}', 'auto', 2, 1),
  ('tpl_code_review', 'Code Review', 'code-review', 'Review code for bugs, security issues, and best practices', 'code-review', 'Review the following code for bugs, security issues, and best practices: {code}', 'auto', 2, 1),
  ('tpl_market_research', 'Market Research', 'market-research', 'Research market trends, competitors, and opportunities', 'research', 'Research {industry} market trends, competitors, and opportunities', 'auto', 3, 1),
  ('tpl_social_posts', 'Social Media Posts', 'social-media-posts', 'Create social media posts for any platform', 'social-media', 'Create {count} social media posts about {topic} for {platform}', 'auto', 1, 1);
