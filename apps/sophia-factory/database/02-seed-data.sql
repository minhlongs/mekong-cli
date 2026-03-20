-- Sophia AI Factory - Seed Data
-- Run after schema is applied

-- Insert a demo organization
INSERT INTO organizations (id, name, slug, plan, proposals_remaining)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Demo Agency', 'demo-agency', 'starter', 10)
ON CONFLICT (id) DO NOTHING;

-- Insert demo user (you'll need to match with Supabase Auth)
INSERT INTO users (id, email, org_id, role)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'admin@demo.agency', '00000000-0000-0000-0000-000000000001', 'admin')
ON CONFLICT (id) DO NOTHING;

-- Insert demo brand voice
INSERT INTO brand_voices (id, org_id, training_docs_count, model_status, voice_characteristics)
VALUES
  (
    '00000000-0000-0000-0000-000000000001',
    '00000000-0000-0000-0000-000000000001',
    0,
    'not_trained',
    '{"tone": "professional", "style": "consultative", "formality": "business"}'
  )
ON CONFLICT (id) DO NOTHING;

-- Insert demo proposals
INSERT INTO proposals (org_id, title, client_name, status, content)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Website Redesign Proposal', 'Acme Corp', 'draft', '{"sections": []}'),
  ('00000000-0000-0000-0000-000000000001', 'Marketing Campaign', 'Beta Inc', 'pending', '{"sections": []}'),
  ('00000000-0000-0000-0000-000000000001', 'SEO Optimization', 'Gamma LLC', 'completed', '{"sections": []}')
ON CONFLICT ON CONSTRAINT proposals_pkey DO NOTHING;

-- Insert demo templates
INSERT INTO templates (name, category, sections, is_public)
VALUES
  ('Standard Proposal', 'proposal', '{"intro": "", "scope": "", "pricing": ""}', true),
  ('SOW Template', 'contract', '{"deliverables": [], "timeline": ""}', true),
  ('NDA Agreement', 'legal', '{"parties": "", "terms": ""}', true),
  ('Discovery Questionnaire', 'discovery', '{"questions": []}', false)
ON CONFLICT ON CONSTRAINT templates_pkey DO NOTHING;

-- Insert demo training documents
INSERT INTO training_documents (org_id, file_url, file_name, file_type, processed)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'https://example.com/doc1.pdf', 'Brand Guidelines.pdf', 'application/pdf', false),
  ('00000000-0000-0000-0000-000000000001', 'https://example.com/doc2.pdf', 'Case Study.pdf', 'application/pdf', false)
ON CONFLICT ON CONSTRAINT training_documents_pkey DO NOTHING;

-- Verification query
SELECT
  'organizations' as table_name, COUNT(*) as row_count FROM organizations
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'brand_voices', COUNT(*) FROM brand_voices
UNION ALL
SELECT 'proposals', COUNT(*) FROM proposals
UNION ALL
SELECT 'templates', COUNT(*) FROM templates
UNION ALL
SELECT 'training_documents', COUNT(*) FROM training_documents;
