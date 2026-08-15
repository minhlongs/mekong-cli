import type { Id, Priority, Status, Timestamp } from './common.js';

export interface AgentDefinition {
  name: string;
  role: string;
  goal: string;
  backstory?: string;
  tools: string[];
  constraints: {
    max_iterations: number;
    max_tokens_per_turn: number;
    require_tests: boolean;
    sandbox: boolean;
  };
  model: {
    provider: string;
    model: string;
    temperature: number;
  };
  memory: {
    type: 'session' | 'persistent' | 'shared';
    max_context: number;
  };
}

export interface AgentInstance {
  id: Id;
  definition: AgentDefinition;
  status: Status;
  currentTask?: TaskAssignment;
  tokenUsage: { input: number; output: number };
  startedAt: Timestamp;
}

export interface TaskAssignment {
  id: Id;
  description: string;
  parentTaskId?: Id;
  agentId: Id;
  priority: Priority;
  inputs: Record<string, unknown>;
  expectedOutputs: string[];
  timeout: number;
  retryCount: number;
  maxRetries: number;
}

export interface AgentMessage {
  id: Id;
  from: string;
  to: string;
  type: 'task' | 'result' | 'query' | 'error' | 'status';
  payload: {
    content: string;
    metadata: Record<string, unknown>;
    artifacts: string[];
  };
  timestamp: Timestamp;
  parentId?: Id;
  priority: Priority;
}

export type OrchestrationPattern = 'hierarchical' | 'sequential' | 'graph' | 'reactive';
