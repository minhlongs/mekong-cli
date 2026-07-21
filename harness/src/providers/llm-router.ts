/**
 * LLM Router - Universal endpoint for all LLM providers
 * 3 vars: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
 */

import { LLMEndpoint, LLMRequest, LLMResponse, LLMMessage, LLMTool } from '../core/types';

export class LLMRouter {
  private endpoint: LLMEndpoint | null;

  constructor(endpoint: LLMEndpoint | null) {
    this.endpoint = endpoint;
  }

  setEndpoint(endpoint: LLMEndpoint): void {
    this.endpoint = endpoint;
  }

  getEndpoint(): LLMEndpoint | null {
    return this.endpoint;
  }

  async complete(request: LLMRequest): Promise<LLMResponse> {
    if (!this.endpoint) {
      throw new Error('No LLM endpoint configured');
    }

    return this.providerRequest(this.endpoint, request);
  }

  async *stream(request: LLMRequest): AsyncGenerator<LLMResponse> {
    if (!this.endpoint) {
      throw new Error('No LLM endpoint configured');
    }

    // For now, delegate to provider-specific streaming
    // In practice, each provider has different streaming APIs
    const response = await this.providerRequest(this.endpoint, { ...request, stream: true });
    yield response;
  }

  private async providerRequest(endpoint: LLMEndpoint, request: LLMRequest): Promise<LLMResponse> {
    const { baseUrl, apiKey, model, provider } = endpoint;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
    };

    // Provider-specific adjustments
    const payload = this.adaptPayloadForProvider(provider, model, request);

    const url = this.getProviderUrl(baseUrl, provider);

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`LLM API error (${response.status}): ${error}`);
    }

    const data = await response.json();
    return data as LLMResponse;
  }

  private adaptPayloadForProvider(provider: string, model: string, request: LLMRequest): any {
    const basePayload = {
      model,
      messages: request.messages,
      temperature: request.temperature ?? 0.7,
      max_tokens: request.maxTokens ?? 4096,
      tools: request.tools,
      tool_choice: request.toolChoice,
      stream: request.stream ?? false,
    };

    switch (provider) {
      case 'anthropic':
        // Anthropic uses different format
        return {
          model,
          messages: request.messages.map(m => ({
            role: m.role === 'system' ? 'user' : m.role,
            content: m.content,
          })),
          system: request.messages.find(m => m.role === 'system')?.content,
          max_tokens: request.maxTokens ?? 4096,
          temperature: request.temperature ?? 0.7,
          tools: request.tools?.map(t => ({
            name: t.function.name,
            description: t.function.description,
            input_schema: t.function.parameters,
          })),
        };

      case 'openrouter':
      case 'openai':
      case 'dashscope':
      case 'google':
        return basePayload;

      case 'ollama':
        return {
          ...basePayload,
          // Ollama uses different parameter names
          options: {
            temperature: request.temperature,
            num_predict: request.maxTokens,
          },
        };

      default:
        return basePayload;
    }
  }

  private getProviderUrl(baseUrl: string, provider: string): string {
    if (baseUrl.endsWith('/v1') || baseUrl.endsWith('/chat/completions')) {
      return baseUrl;
    }

    switch (provider) {
      case 'anthropic':
        return `${baseUrl.replace(/\/+$/, '')}/v1/messages`;
      case 'openrouter':
        return `${baseUrl.replace(/\/+$/, '')}/v1/chat/completions`;
      case 'openai':
        return `${baseUrl.replace(/\/+$/, '')}/v1/chat/completions`;
      case 'dashscope':
        return `${baseUrl.replace(/\/+$/, '')}/v1/chat/completions`;
      case 'google':
        return `${baseUrl.replace(/\/+$/, '')}/v1beta/models/${this.endpoint?.model}:generateContent`;
      case 'ollama':
        return `${baseUrl.replace(/\/+$/, '')}/api/chat`;
      default:
        return `${baseUrl.replace(/\/+$/, '')}/v1/chat/completions`;
    }
  }

  // Factory method to create from environment
  static fromEnv(): LLMRouter {
    const baseUrl = process.env.LLM_BASE_URL || 'https://api.anthropic.com';
    const apiKey = process.env.LLM_API_KEY || process.env.ANTHROPIC_API_KEY || process.env.OPENROUTER_API_KEY;
    const model = process.env.LLM_MODEL || 'claude-fable-5';
    const provider = (process.env.LLM_PROVIDER as any) || 'anthropic';

    if (!apiKey && provider !== 'ollama' && provider !== 'offline') {
      console.warn('[LLMRouter] No API key found, LLM calls will fail');
    }

    return new LLMRouter({
      baseUrl,
      apiKey: apiKey || '',
      model,
      provider,
    });
  }
}

/**
 * Provider preset configurations
 */
export const PROVIDER_PRESETS = {
  anthropic: {
    provider: 'anthropic' as const,
    baseUrl: 'https://api.anthropic.com',
    models: ['claude-fable-5', 'claude-opus-4-8', 'claude-opus-4-7', 'claude-sonnet-4-7', 'claude-haiku-4-5'],
  },
  openrouter: {
    provider: 'openrouter' as const,
    baseUrl: 'https://openrouter.ai/api/v1',
    models: ['anthropic/claude-opus-4', 'anthropic/claude-sonnet-4', 'google/gemini-2.5-pro', 'qwen/qwen3-5-plus'],
  },
  dashscope: {
    provider: 'dashscope' as const,
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: ['qwen3.5-plus', 'qwen3.5-max', 'qwen-turbo'],
  },
  google: {
    provider: 'google' as const,
    baseUrl: 'https://generativelanguage.googleapis.com',
    models: ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro'],
  },
  ollama: {
    provider: 'ollama' as const,
    baseUrl: 'http://localhost:11434',
    models: ['llama3.2:3b', 'qwen2.5:7b', 'deepseek-coder-v2:16b'],
  },
} as const;

/**
 * Get endpoint config from preset + overrides
 */
export function createEndpointFromPreset(
  presetName: keyof typeof PROVIDER_PRESETS,
  apiKey: string,
  model?: string
): LLMEndpoint {
  const preset = PROVIDER_PRESETS[presetName];
  return {
    provider: preset.provider,
    baseUrl: preset.baseUrl,
    apiKey,
    model: model || preset.models[0],
  };
}