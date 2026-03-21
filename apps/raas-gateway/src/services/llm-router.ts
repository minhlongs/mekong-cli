/**
 * LLM Router — selects model based on mission complexity and executes via CF Workers AI.
 * Supports complexity-based routing with automatic fallback chain.
 */

import type { Ai } from '@cloudflare/workers-types';

// Model map by complexity
const MODEL_MAP: Record<string, string> = {
  simple:   '@cf/meta/llama-3.1-8b-instruct',
  standard: '@cf/meta/llama-3.1-70b-instruct',
  complex:  '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
};

// Explicit preference overrides (e.g. from mission.model column)
const PREFERENCE_MAP: Record<string, string> = {
  auto:     '@cf/meta/llama-3.1-8b-instruct',
  fast:     '@cf/meta/llama-3.1-8b-instruct',
  balanced: '@cf/meta/llama-3.1-70b-instruct',
  premium:  '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
};

// Fallback chain — tried in order when primary model fails
const FALLBACK_CHAIN = [
  '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
  '@cf/meta/llama-3.1-70b-instruct',
  '@cf/meta/llama-3.1-8b-instruct',
];

const MAX_TOKENS_MAP: Record<string, number> = {
  simple:   512,
  standard: 1024,
  complex:  2048,
};

export interface LlmRequest {
  goal: string;
  complexity: string;
  /** Optional model preference override (auto | fast | balanced | premium) */
  modelPreference?: string;
  context?: string;
}

export interface LlmResponse {
  result: string;
  model: string;
  latencyMs: number;
}

export class LlmRouter {
  constructor(private ai: Ai) {}

  /**
   * Resolve which model to use: preference override > complexity map
   */
  resolveModel(complexity: string, preference?: string): string {
    if (preference && PREFERENCE_MAP[preference]) {
      return PREFERENCE_MAP[preference];
    }
    return MODEL_MAP[complexity] || MODEL_MAP.standard;
  }

  /**
   * Build system prompt based on complexity
   */
  private buildSystemPrompt(complexity: string): string {
    const base = 'You are Mekong CLI, an AI business operations assistant. ';
    switch (complexity) {
      case 'simple':
        return base + 'Give a brief, actionable answer in 2-3 paragraphs.';
      case 'complex':
        return base + 'Provide a comprehensive plan with steps, code examples, and considerations. Be thorough.';
      default:
        return base + 'Provide a clear, structured response with actionable steps.';
    }
  }

  /**
   * Execute request against a single model — throws on failure
   */
  private async runModel(model: string, req: LlmRequest): Promise<string> {
    const userContent = req.context
      ? `${req.goal}\n\nContext: ${req.context}`
      : req.goal;

    const response = await this.ai.run(model as Parameters<Ai['run']>[0], {
      messages: [
        { role: 'system', content: this.buildSystemPrompt(req.complexity) },
        { role: 'user',   content: userContent },
      ],
      max_tokens: MAX_TOKENS_MAP[req.complexity] ?? 1024,
    }) as { response?: string } | string;

    return typeof response === 'string'
      ? response
      : response?.response || 'No response generated';
  }

  /**
   * Execute with fallback chain — tries primary model first, then remaining fallbacks
   */
  async execute(req: LlmRequest): Promise<LlmResponse> {
    const primary = this.resolveModel(req.complexity, req.modelPreference);
    const startTime = Date.now();

    // Build ordered attempt list: primary first, then remaining fallbacks
    const chain = [primary, ...FALLBACK_CHAIN.filter(m => m !== primary)];

    for (const model of chain) {
      try {
        const result = await this.runModel(model, req);
        return { result, model, latencyMs: Date.now() - startTime };
      } catch (err) {
        console.error(`[LlmRouter] ${model} failed:`, (err as Error).message);
      }
    }

    throw new Error('All LLM models failed — no fallback succeeded');
  }
}
