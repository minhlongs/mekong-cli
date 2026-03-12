/**
 * CostCalculator — map provider/model to per-token cost in USD.
 * Supports: anthropic, openai, ollama (free), openrouter, deepseek.
 */

/** Pricing: [inputCostPerMToken, outputCostPerMToken] in USD */
const PRICING: Record<string, [number, number]> = {
  // Anthropic
  'anthropic/claude-sonnet-4-20250514': [3.0, 15.0],
  'anthropic/claude-sonnet-4': [3.0, 15.0],
  'anthropic/claude-haiku-4-5-20251001': [0.8, 4.0],
  'anthropic/claude-opus-4-6': [15.0, 75.0],
  // OpenAI
  'openai/gpt-4o': [2.5, 10.0],
  'openai/gpt-4o-mini': [0.15, 0.6],
  'openai/gpt-3.5-turbo': [0.5, 1.5],
  // DeepSeek
  'openai/deepseek-chat': [0.14, 0.28],
  'openai/deepseek-reasoner': [0.55, 2.19],
  // OpenRouter — use model name directly
  'openrouter/anthropic/claude-sonnet-4': [3.0, 15.0],
  'openrouter/openai/gpt-4o': [2.5, 10.0],
  // Standalone model keys (without provider prefix)
  'claude-sonnet-4-20250514': [3.0, 15.0],
  'claude-sonnet-4': [3.0, 15.0],
  'claude-haiku-4-5-20251001': [0.8, 4.0],
  'claude-opus-4-6': [15.0, 75.0],
  'gpt-4o': [2.5, 10.0],
  'gpt-4o-mini': [0.15, 0.6],
  'gpt-3.5-turbo': [0.5, 1.5],
  'deepseek-chat': [0.14, 0.28],
  'deepseek-reasoner': [0.55, 2.19],
};

/** Providers whose models are always free */
const FREE_PROVIDERS = new Set(['ollama', 'local', 'cloudflare-workers-ai']);

export class CostCalculator {
  /**
   * Calculate cost in USD for a completed LLM call.
   * @param provider - provider name (e.g. 'anthropic', 'ollama')
   * @param model - model name (e.g. 'claude-sonnet-4-20250514')
   * @param inputTokens - number of input tokens
   * @param outputTokens - number of output tokens
   */
  calculate(provider: string, model: string, inputTokens: number, outputTokens: number): number {
    if (FREE_PROVIDERS.has(provider.toLowerCase())) return 0;

    // Try provider/model key first, then bare model key
    const providerModelKey = `${provider.toLowerCase()}/${model}`;
    const pricing = PRICING[providerModelKey] ?? PRICING[model] ?? null;

    if (!pricing) {
      // Unknown model: use a conservative default (Sonnet-level)
      return (inputTokens / 1_000_000) * 3.0 + (outputTokens / 1_000_000) * 15.0;
    }

    return (inputTokens / 1_000_000) * pricing[0] + (outputTokens / 1_000_000) * pricing[1];
  }

  /**
   * Get pricing for a provider/model pair.
   * @returns [inputCostPerMToken, outputCostPerMToken] in USD, or null if unknown
   */
  getPricing(provider: string, model: string): [number, number] | null {
    if (FREE_PROVIDERS.has(provider.toLowerCase())) return [0, 0];
    const key = `${provider.toLowerCase()}/${model}`;
    return PRICING[key] ?? PRICING[model] ?? null;
  }

  /** List all known provider/model keys in the pricing table. */
  knownModels(): string[] {
    return Object.keys(PRICING);
  }

  /** Check whether a provider is free */
  isFreeProvider(provider: string): boolean {
    return FREE_PROVIDERS.has(provider.toLowerCase());
  }
}
