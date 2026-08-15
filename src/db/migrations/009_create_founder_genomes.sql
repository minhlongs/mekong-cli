-- Founder Genome Capture System
-- Stores encrypted founder profile data for AI-assisted analysis

CREATE TABLE IF NOT EXISTS founder_genomes (
    id SERIAL PRIMARY KEY,
    founder_id VARCHAR(255) NOT NULL UNIQUE,
    encrypted_data BYTEA NOT NULL,          -- AES-256-GCM encrypted JSON
    encryption_key_id VARCHAR(100) NOT NULL, -- Key identifier for key rotation
    genome_hash VARCHAR(64) NOT NULL,       -- SHA-256 hash for deduplication
    analysis_summary TEXT,                   -- AI-generated insights
    confidence_score DECIMAL(3,2),          -- AI confidence 0.00-1.00
    trait_scores JSONB DEFAULT '{}',        -- Extracted founder traits
    cluster_id INTEGER,                      -- For grouping similar founders
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_founder_genomes_founder_id ON founder_genomes(founder_id);
CREATE INDEX IF NOT EXISTS idx_founder_genomes_hash ON founder_genomes(genome_hash);
CREATE INDEX IF NOT EXISTS idx_founder_genomes_cluster ON founder_genomes(cluster_id);
CREATE INDEX IF NOT EXISTS idx_founder_genomes_confidence ON founder_genomes(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_founder_genomes_created ON founder_genomes(created_at DESC);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_founder_genomes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_founder_genomes_updated_at ON founder_genomes;
CREATE TRIGGER update_founder_genomes_updated_at BEFORE UPDATE ON founder_genomes
    FOR EACH ROW EXECUTE FUNCTION update_founder_genomes_updated_at();
