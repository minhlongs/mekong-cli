-- Behavior Graph Service Schema
-- Migration 014: Graph tables for entity relationships and behavior tracking
-- Uses PostgreSQL JSONB for flexible attribute storage
-- Migration date: 2026-06-18

-- Entities table: nodes in the behavior graph
CREATE TABLE IF NOT EXISTS graph_entities (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Graph edges table: directed relationships between entities
CREATE TABLE IF NOT EXISTS graph_edges (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    target_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    edge_type VARCHAR(100) NOT NULL,
    weight DECIMAL(5,4) DEFAULT 1.0000 CHECK (weight >= 0),
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, edge_type)
);

-- Behaviors table: actions/events performed by entities
CREATE TABLE IF NOT EXISTS graph_behaviors (
    id VARCHAR(255) PRIMARY KEY,
    entity_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    context JSONB DEFAULT '{}',
    outcome JSONB,
    confidence DECIMAL(3,2) DEFAULT 1.00 CHECK (confidence >= 0 AND confidence <= 1),
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trust relationships: bidirectional trust scores
CREATE TABLE IF NOT EXISTS graph_trust (
    id VARCHAR(255) PRIMARY KEY,
    source_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    target_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    score DECIMAL(4,3) NOT NULL CHECK (score >= -1.0 AND score <= 1.0),
    weight DECIMAL(5,4) DEFAULT 1.0000 CHECK (weight >= 0),
    rationale TEXT,
    evidence JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id)
);

-- Intents: declared or inferred goals/intentions
CREATE TABLE IF NOT EXISTS graph_intents (
    id VARCHAR(255) PRIMARY KEY,
    entity_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    intent_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 1.00 CHECK (confidence >= 0 AND confidence <= 1),
    status VARCHAR(50) DEFAULT 'active',
    related_entities JSONB DEFAULT '[]',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Predictions: ML-generated forecasts
CREATE TABLE IF NOT EXISTS graph_predictions (
    id VARCHAR(255) PRIMARY KEY,
    entity_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    prediction_type VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    features JSONB DEFAULT '{}',
    model_version VARCHAR(100) NOT NULL,
    validated BOOLEAN DEFAULT FALSE,
    actual_outcome JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Actions: recommended or executed actions
CREATE TABLE IF NOT EXISTS graph_actions (
    id VARCHAR(255) PRIMARY KEY,
    entity_id VARCHAR(255) NOT NULL REFERENCES graph_entities(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',
    priority INTEGER DEFAULT 1 CHECK (priority >= 1 AND priority <= 10),
    status VARCHAR(50) DEFAULT 'pending',
    context JSONB DEFAULT '{}',
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_graph_entities_type ON graph_entities(type);
CREATE INDEX IF NOT EXISTS idx_graph_entities_name ON graph_entities(name);

CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_graph_edges_source_target ON graph_edges(source_id, target_id);

-- GIN indexes for JSONB fields (enables efficient containment queries)
CREATE INDEX IF NOT EXISTS idx_graph_entities_properties ON graph_entities USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_graph_edges_properties ON graph_edges USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_graph_behaviors_context ON graph_behaviors USING GIN (context);
CREATE INDEX IF NOT EXISTS idx_graph_behaviors_outcome ON graph_behaviors USING GIN (outcome);
CREATE INDEX IF NOT EXISTS idx_graph_trust_evidence ON graph_trust USING GIN (evidence);
CREATE INDEX IF NOT EXISTS idx_graph_intents_related ON graph_intents USING GIN (related_entities);
CREATE INDEX IF NOT EXISTS idx_graph_predictions_features ON graph_predictions USING GIN (features);
CREATE INDEX IF NOT EXISTS idx_graph_predictions_value ON graph_predictions USING GIN (value);
CREATE INDEX IF NOT EXISTS idx_graph_actions_parameters ON graph_actions USING GIN (parameters);
CREATE INDEX IF NOT EXISTS idx_graph_actions_context ON graph_actions USING GIN (context);

-- Indexes for timestamp-based queries
CREATE INDEX IF NOT EXISTS idx_graph_behaviors_timestamp ON graph_behaviors(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_graph_behaviors_entity ON graph_behaviors(entity_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_graph_predictions_created ON graph_predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_graph_actions_created ON graph_actions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_graph_actions_status ON graph_actions(status);
CREATE INDEX IF NOT EXISTS idx_graph_intents_status ON graph_intents(status);
CREATE INDEX IF NOT EXISTS idx_graph_intents_entity ON graph_intents(entity_id, status);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_graph_trust_pair ON graph_trust(source_id, target_id) INCLUDE (score, weight);
CREATE INDEX IF NOT EXISTS idx_graph_edges_pair_type ON graph_edges(source_id, target_id, edge_type) INCLUDE (weight);
