-- Migration 0016: Create mission_templates table and seed 22 templates
CREATE TABLE IF NOT EXISTS mission_templates (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL, -- content, code, research, marketing, sales, support
  default_complexity TEXT DEFAULT 'standard',
  estimated_credits INTEGER DEFAULT 2,
  example_goal TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

INSERT INTO mission_templates (id, title, description, category, default_complexity, estimated_credits, example_goal) VALUES
('tpl-content-blog', 'Blog Post Writer', 'Write a professional blog post on any topic', 'content', 'standard', 2, 'Write a 1000-word blog post about AI automation'),
('tpl-content-social', 'Social Media Pack', 'Create social media posts for multiple platforms', 'content', 'simple', 1, 'Create Twitter, LinkedIn, Instagram posts about product launch'),
('tpl-content-email', 'Email Campaign', 'Draft email marketing campaign', 'content', 'standard', 2, 'Write 5-email drip sequence for SaaS onboarding'),
('tpl-content-landing', 'Landing Page Copy', 'Write conversion-focused landing page copy', 'content', 'complex', 3, 'Write hero, features, pricing, CTA sections'),
('tpl-code-review', 'Code Review', 'Review code for bugs, security, and best practices', 'code', 'standard', 2, 'Review authentication module for security issues'),
('tpl-code-refactor', 'Code Refactor', 'Refactor code for better maintainability', 'code', 'complex', 3, 'Refactor user service to use repository pattern'),
('tpl-code-test', 'Test Generator', 'Generate unit and integration tests', 'code', 'standard', 2, 'Write tests for payment processing module'),
('tpl-code-docs', 'API Documentation', 'Generate API documentation from code', 'code', 'simple', 1, 'Document REST API endpoints with examples'),
('tpl-research-market', 'Market Research', 'Research market size, competitors, trends', 'research', 'complex', 3, 'Research AI SaaS market in Southeast Asia'),
('tpl-research-tech', 'Tech Stack Analysis', 'Compare technologies for a specific use case', 'research', 'standard', 2, 'Compare Next.js vs Remix vs Astro for docs site'),
('tpl-research-competitor', 'Competitor Analysis', 'Analyze competitor products and positioning', 'research', 'complex', 3, 'Analyze top 5 AI automation platforms'),
('tpl-research-user', 'User Research Plan', 'Create user research methodology and questions', 'research', 'standard', 2, 'Design user interview questions for developer tools'),
('tpl-marketing-seo', 'SEO Strategy', 'Create SEO keyword strategy and content plan', 'marketing', 'complex', 3, 'Build SEO strategy for developer tools SaaS'),
('tpl-marketing-launch', 'Product Launch Plan', 'Create go-to-market launch strategy', 'marketing', 'complex', 3, 'Plan Product Hunt launch for CLI tool'),
('tpl-marketing-ads', 'Ad Copy Generator', 'Write Google/Facebook ad copy variations', 'marketing', 'simple', 1, 'Create 10 ad variations for SaaS product'),
('tpl-sales-pitch', 'Sales Pitch Deck', 'Create sales presentation outline and talking points', 'sales', 'complex', 3, 'Create enterprise sales deck for AI platform'),
('tpl-sales-email', 'Cold Outreach Email', 'Write personalized cold outreach sequences', 'sales', 'standard', 2, 'Write 3-email cold outreach for CTO persona'),
('tpl-sales-proposal', 'Proposal Generator', 'Generate client proposal document', 'sales', 'complex', 3, 'Create proposal for enterprise AI integration'),
('tpl-support-faq', 'FAQ Generator', 'Generate FAQ from product documentation', 'support', 'simple', 1, 'Create 20-question FAQ for developer API'),
('tpl-support-kb', 'Knowledge Base Article', 'Write support knowledge base articles', 'support', 'standard', 2, 'Write troubleshooting guide for API authentication'),
('tpl-support-onboard', 'Onboarding Guide', 'Create user onboarding documentation', 'support', 'standard', 2, 'Write quickstart guide for new API users'),
('tpl-general-summary', 'Document Summarizer', 'Summarize long documents into key points', 'content', 'simple', 1, 'Summarize 50-page technical whitepaper');
