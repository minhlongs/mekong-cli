/**
 * OpenClaw Model Registry — catalog of available LLM providers and models
 * Mirrors the provider config from openclaw.json
 */

export interface ModelInfo {
  id: string;
  provider: string;
  name: string;
  contextWindow: number;
  maxTokens: number;
  capabilities: string[];
  costPerMToken: { input: number; output: number };
  status: 'available' | 'degraded' | 'offline';
}

export interface ModelFilter {
  provider?: string;
  capability?: string;
}

export interface ModelRequirements {
  capability?: string;
  maxCost?: number;
  minContext?: number;
}

const MODELS: ModelInfo[] = [
  {
    id: 'qwen3.5-plus',
    provider: 'bailian',
    name: 'Qwen 3.5 Plus',
    contextWindow: 1000000,
    maxTokens: 65536,
    capabilities: ['text', 'image', 'code', 'reasoning'],
    costPerMToken: { input: 0.5, output: 1.5 },
    status: 'available',
  },
  {
    id: 'qwen3-coder-plus',
    provider: 'bailian',
    name: 'Qwen 3 Coder Plus',
    contextWindow: 1000000,
    maxTokens: 65536,
    capabilities: ['text', 'code'],
    costPerMToken: { input: 0.3, output: 0.9 },
    status: 'available',
  },
  {
    id: 'minimax-m2.5',
    provider: 'bailian',
    name: 'MiniMax M2.5',
    contextWindow: 204800,
    maxTokens: 131072,
    capabilities: ['text', 'long-output'],
    costPerMToken: { input: 0.2, output: 0.6 },
    status: 'available',
  },
  {
    id: 'kimi-k2.5',
    provider: 'bailian',
    name: 'Kimi K2.5',
    contextWindow: 262144,
    maxTokens: 32768,
    capabilities: ['text', 'image', 'reasoning'],
    costPerMToken: { input: 0.4, output: 1.2 },
    status: 'available',
  },
  {
    id: 'glm-5',
    provider: 'bailian',
    name: 'GLM-5',
    contextWindow: 202752,
    maxTokens: 16384,
    capabilities: ['text', 'general'],
    costPerMToken: { input: 0.2, output: 0.6 },
    status: 'available',
  },
  {
    id: 'claude-sonnet-4',
    provider: 'anthropic',
    name: 'Claude Sonnet 4',
    contextWindow: 200000,
    maxTokens: 64000,
    capabilities: ['text', 'image', 'code', 'reasoning', 'tool-use'],
    costPerMToken: { input: 3, output: 15 },
    status: 'available',
  },
  {
    id: 'gpt-4o',
    provider: 'openai',
    name: 'GPT-4o',
    contextWindow: 128000,
    maxTokens: 16384,
    capabilities: ['text', 'image', 'code', 'tool-use'],
    costPerMToken: { input: 2.5, output: 10 },
    status: 'available',
  },
];

export class OpenClawModelRegistry {
  private readonly models: ModelInfo[] = MODELS;

  /** List models with optional provider/capability filters */
  listModels(filter?: ModelFilter): ModelInfo[] {
    let result = this.models;
    if (filter?.provider) result = result.filter(m => m.provider === filter.provider);
    if (filter?.capability) result = result.filter(m => m.capabilities.includes(filter.capability!));
    return result;
  }

  /** Get single model by id */
  getModel(id: string): ModelInfo | undefined {
    return this.models.find(m => m.id === id);
  }

  /**
   * Select the cheapest available model matching given requirements.
   * Filters by capability, minContext, and maxCost (input $/M tokens).
   */
  selectOptimal(requirements: ModelRequirements): ModelInfo | undefined {
    let candidates = this.models.filter(m => m.status === 'available');
    if (requirements.capability) {
      candidates = candidates.filter(m => m.capabilities.includes(requirements.capability!));
    }
    if (requirements.minContext) {
      candidates = candidates.filter(m => m.contextWindow >= requirements.minContext!);
    }
    if (requirements.maxCost !== undefined) {
      candidates = candidates.filter(m => m.costPerMToken.input <= requirements.maxCost!);
    }
    // Cheapest input cost first
    candidates.sort((a, b) => a.costPerMToken.input - b.costPerMToken.input);
    return candidates[0];
  }
}
