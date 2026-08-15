import type { Id, Timestamp } from './common.js';

export interface SessionEntry {
  id: Id;
  sessionId: Id;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  metadata: {
    model?: string;
    tokens?: { input: number; output: number };
    tool?: string;
    timestamp: Timestamp;
  };
}

export interface KnowledgeEntity {
  id: Id;
  type: 'fact' | 'procedure' | 'concept' | 'reference';
  content: string;
  source: string;
  tags: string[];
  embedding?: number[];
  createdAt: Timestamp;
  updatedAt: Timestamp;
  accessCount: number;
}

export interface IdentityConfig {
  name: string;
  role: string;
  principles: string[];
  communication_style: {
    tone: string;
    format: string;
    language: string;
  };
  working_hours?: {
    timezone: string;
    start: string;
    end: string;
  };
}

export interface KaizenSuggestion {
  id: Id;
  category: 'performance' | 'quality' | 'process' | 'tooling';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  createdAt: Timestamp;
  applied: boolean;
  appliedAt?: Timestamp;
}
