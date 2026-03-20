-- Sophia AI Factory Database Schema
-- Run this in Supabase SQL Editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Organizations (Agencies)
CREATE TABLE IF NOT EXISTS organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'starter',
  proposals_remaining INTEGER DEFAULT 10,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  org_id UUID REFERENCES organizations(id),
  role TEXT DEFAULT 'member',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Brand Voices
CREATE TABLE IF NOT EXISTS brand_voices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id) UNIQUE,
  training_docs_count INTEGER DEFAULT 0,
  model_status TEXT DEFAULT 'not_trained',
  voice_characteristics JSONB,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Proposals
CREATE TABLE IF NOT EXISTS proposals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id),
  title TEXT NOT NULL,
  client_name TEXT,
  status TEXT DEFAULT 'draft',
  content JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Templates
CREATE TABLE IF NOT EXISTS templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  category TEXT,
  sections JSONB,
  is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training Documents
CREATE TABLE IF NOT EXISTS training_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID REFERENCES organizations(id),
  file_url TEXT NOT NULL,
  file_name TEXT,
  file_type TEXT,
  processed BOOLEAN DEFAULT false,
  content_text TEXT,
  embedding vector(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_voices ENABLE ROW LEVEL SECURITY;
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_documents ENABLE ROW LEVEL SECURITY;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_proposals_org_id ON proposals(org_id);
CREATE INDEX IF NOT EXISTS idx_training_docs_org_id ON training_documents(org_id);
CREATE INDEX IF NOT EXISTS idx_brand_voices_org_id ON brand_voices(org_id);

-- pgvector similarity search function for training documents
CREATE OR REPLACE FUNCTION match_training_documents(
  query_embedding vector(1536),
  match_org_id uuid,
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  file_name text,
  file_url text,
  content_text text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    training_documents.id,
    training_documents.file_name,
    training_documents.file_url,
    training_documents.content_text,
    1 - (training_documents.embedding <=> query_embedding) AS similarity
  FROM training_documents
  WHERE training_documents.org_id = match_org_id
    AND 1 - (training_documents.embedding <=> query_embedding) > match_threshold
  ORDER BY training_documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- pgvector similarity search function for brand voices
CREATE OR REPLACE FUNCTION match_brand_voices(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id uuid,
  org_id uuid,
  voice_characteristics jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    brand_voices.id,
    brand_voices.org_id,
    brand_voices.voice_characteristics,
    1 - (brand_voices.embedding <=> query_embedding) AS similarity
  FROM brand_voices
  WHERE brand_voices.embedding IS NOT NULL
    AND 1 - (brand_voices.embedding <=> query_embedding) > match_threshold
  ORDER BY brand_voices.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
