/**
 * LLM Router — routes requests to the correct provider.
 * Features: multi-provider, automatic fallback, cost tracking.
 */
import type { ChatRequest, ChatResponse, LlmProvider } from './types.js';
import type { MekongConfig } from '../types/config.js';
import { CostTracker } from './cost-tracker.js';
import { OpenAICompatProvider } from './providers/openai-compatible.js';
import { OllamaProvider } from './providers/ollama.js';
import { AnthropicProvider } from './providers/anthropic.js';
import { OpenAIProvider } from './providers/openai.js';
import { LocalProvider } from './providers/local.js';
import { MekongError } from '../types/common.js';
import { emit } from '../core/events.js';
import type { MeteringCollector } from '../metering/collector.js';

/** Provider factory configs */
const PROVIDER_DEFAULTS: Record<string, { baseUrl: string; defaultModel: string }> = {
  anthropic: { baseUrl: 'https://api.anthropic.com/v1', defaultModel: 'claude-sonnet-4-20250514' },
  openai: { baseUrl: 'https://api.openai.com/v1', defaultModel: 'gpt-4o' },
  deepseek: { baseUrl: 'https://api.deepseek.com/v1', defaultModel: 'deepseek-chat' },
  openrouter: { baseUrl: 'https://openrouter.ai/api/v1', defaultModel: 'anthropic/claude-sonnet-4' },
};

/** Environment variable names for API keys */
const ENV_KEY_MAP: Record<string, string> = {
  anthropic: 'ANTHROPIC_API_KEY',
  openai: 'OPENAI_API_KEY',
  deepseek: 'DEEPSEEK_API_KEY',
  openrouter: 'OPENROUTER_API_KEY',
};

export class LlmRouter {
  private providers: Map<string, LlmProvider> = new Map();
  private defaultProvider: string;
  private defaultModel: string;
  readonly costTracker: CostTracker;
  private meteringCollector: MeteringCollector | null = null;

  constructor(config: MekongConfig) {
    this.costTracker = new CostTracker();
    this.defaultProvider = config.llm.default_provider;
    this.defaultModel = config.llm.default_model;
    this.initProviders(config);
  }

  /** Attach a MeteringCollector to auto-record every LLM call */
  attachMetering(collector: MeteringCollector): void {
    this.meteringCollector = collector;
  }

  /** Send a chat request, with automatic fallback */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const providerName = request.provider ?? this.defaultProvider;
    const provider = this.providers.get(providerName);

    if (provider) {
      try {
        const response = await provider.chat({
          ...request,
          model: request.model ?? this.defaultModel,
        });
        const costRecord = this.costTracker.record(
          response.provider, response.model,
          response.usage.inputTokens, response.usage.outputTokens,
          response.latencyMs,
        );
        this.meteringCollector?.recordLlmCall({
          provider: response.provider,
          model: response.model,
          inputTokens: response.usage.inputTokens,
          outputTokens: response.usage.outputTokens,
          durationMs: response.latencyMs,
          estimatedCost: costRecord.cost,
        });
        return response;
      } catch (error) {
        return this.fallback(request, providerName, error);
      }
    }

    return this.fallback(request, providerName, new Error(`Provider "${providerName}" not configured`));
  }

  /** Get available provider names */
  getProviders(): string[] {
    return Array.from(this.providers.keys());
  }

  /** Get usage summary */
  getUsageSummary() {
    return this.costTracker.getSummary();
  }

  /** Try fallback providers in order */
  private async fallback(request: ChatRequest, failedProvider: string, originalError: unknown): Promise<ChatResponse> {
    const fallbackOrder = Array.from(this.providers.keys()).filter(p => p !== failedProvider);

    for (const providerName of fallbackOrder) {
      const provider = this.providers.get(providerName)!;
      try {
        const available = await provider.isAvailable();
        if (!available) continue;

        const response = await provider.chat({
          ...request,
          model: request.model ?? this.defaultModel,
        });
        const fallbackCost = this.costTracker.record(
          response.provider, response.model,
          response.usage.inputTokens, response.usage.outputTokens,
          response.latencyMs,
        );
        this.meteringCollector?.recordLlmCall({
          provider: response.provider,
          model: response.model,
          inputTokens: response.usage.inputTokens,
          outputTokens: response.usage.outputTokens,
          durationMs: response.latencyMs,
          estimatedCost: fallbackCost.cost,
        });
        emit('engine:started', { fallbackFrom: failedProvider, fallbackTo: providerName });
        return response;
      } catch {
        continue;
      }
    }

    throw new MekongError(
      `All LLM providers failed. Original error: ${originalError}`,
      'LLM_ALL_PROVIDERS_FAILED',
      false,
    );
  }

  /** Initialize providers from config */
  private initProviders(config: MekongConfig): void {
    // Check LLM_BASE_URL / LLM_API_KEY env vars (universal endpoint)
    const envBaseUrl = process.env.LLM_BASE_URL;
    const envApiKey = process.env.LLM_API_KEY;
    const envModel = process.env.LLM_MODEL;

    if (envBaseUrl && envApiKey) {
      this.providers.set(this.defaultProvider, new OpenAICompatProvider({
        name: this.defaultProvider,
        baseUrl: envBaseUrl,
        apiKey: envApiKey,
        defaultModel: envModel ?? this.defaultModel,
      }));
    }

    // Register configured providers using native implementations
    for (const [name, providerConfig] of Object.entries(config.llm.providers)) {
      const apiKey = providerConfig.api_key
        ?? (providerConfig.api_key_env ? process.env[providerConfig.api_key_env] : undefined);
      if (!apiKey) continue;

      const defaults = PROVIDER_DEFAULTS[name] ?? { baseUrl: '', defaultModel: '' };
      const baseUrl = providerConfig.base_url ?? defaults.baseUrl;

      this.providers.set(name, this.createProvider(name, apiKey, baseUrl, providerConfig.default_model ?? defaults.defaultModel));
    }

    // Auto-detect from env vars if no providers configured yet
    if (this.providers.size === 0) {
      for (const [providerName, envKey] of Object.entries(ENV_KEY_MAP)) {
        const key = process.env[envKey];
        if (key) {
          const defaults = PROVIDER_DEFAULTS[providerName]!;
          this.providers.set(providerName, this.createProvider(providerName, key, defaults.baseUrl, defaults.defaultModel));
        }
      }

      // CF Workers AI from env
      const cfAccount = process.env.CF_ACCOUNT_ID;
      const cfToken = process.env.CF_API_TOKEN;
      if (cfAccount && cfToken) {
        this.providers.set('cloudflare', new LocalProvider({
          backend: 'cloudflare-workers-ai',
          accountId: cfAccount,
          apiToken: cfToken,
        }));
      }

      // Always add Ollama as last-resort local fallback
      const ollamaUrl = process.env.OLLAMA_BASE_URL ?? 'http://localhost:11434';
      this.providers.set('ollama', new OllamaProvider(ollamaUrl));
    }
  }

  /** Create the best provider implementation for a given name */
  private createProvider(name: string, apiKey: string, baseUrl: string, defaultModel: string): LlmProvider {
    switch (name) {
      case 'anthropic':
        return new AnthropicProvider({ apiKey, baseUrl: baseUrl || undefined, defaultModel });
      case 'openai':
        return new OpenAIProvider({ apiKey, baseUrl: baseUrl || undefined, defaultModel });
      case 'ollama':
        return new OllamaProvider(baseUrl, defaultModel);
      default:
        if (!baseUrl) throw new MekongError(`Provider "${name}" requires a base URL`, 'PROVIDER_CONFIG_ERROR', false);
        return new OpenAICompatProvider({ name, baseUrl, apiKey, defaultModel });
    }
  }
}
