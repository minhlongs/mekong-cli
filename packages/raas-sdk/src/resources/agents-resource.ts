/**
 * Agents resource — browse marketplace, install, execute installed agents
 */

import type { HttpRequester } from '../http-requester.js';

export interface Agent {
  id: string;
  slug: string;
  name: string;
  description: string;
  category: string;
  capability: string;
  modelPreference?: string;
  creditsPerRun: number;
  rating?: number;
  installCount: number;
}

export interface AgentExecuteInput {
  agentId: string;
  input: string;
  metadata?: Record<string, string>;
}

export interface AgentExecuteResult {
  executionId: string;
  output: string;
  creditsUsed: number;
  durationMs: number;
}

export interface AgentListParams {
  category?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export class AgentsResource {
  constructor(private readonly http: HttpRequester) {}

  /** Browse published agents in the marketplace */
  list(params?: AgentListParams): Promise<{ agents: Agent[]; total: number }> {
    return this.http.get('/agents/browse', params as Record<string, string | number | undefined>);
  }

  /** Get agent detail by slug */
  get(slug: string): Promise<Agent> {
    return this.http.get(`/agents/${slug}`);
  }

  /** Install agent to tenant account */
  install(agentId: string): Promise<{ success: boolean; message: string }> {
    return this.http.post(`/agents/${agentId}/install`);
  }

  /** List agents installed by current tenant */
  listInstalled(): Promise<Agent[]> {
    return this.http.get('/agents/installed');
  }

  /** Execute an installed agent */
  execute(input: AgentExecuteInput): Promise<AgentExecuteResult> {
    return this.http.post(`/agents/${input.agentId}/execute`, {
      input: input.input,
      metadata: input.metadata,
    });
  }
}
