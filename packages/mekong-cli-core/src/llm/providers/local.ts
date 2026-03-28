/**
 * Local provider — supports MLX, Ollama, and Cloudflare Workers AI.
 * MLX is preferred on Apple Silicon for optimal performance.
 */
import { OpenAICompatProvider } from './openai-compatible.js';
import type { ChatRequest, ChatResponse, LlmProvider } from '../types.js';

export interface LocalConfig {
  /** 'mlx', 'ollama', or 'cloudflare-workers-ai' */
  backend: 'mlx' | 'ollama' | 'cloudflare-workers-ai';
  baseUrl?: string;
  defaultModel?: string;
  /** Required for CF Workers AI */
  accountId?: string;
  apiToken?: string;
}

export class LocalProvider implements LlmProvider {
  readonly name: string;
  private inner: OpenAICompatProvider;
  private healthUrl: string;

  constructor(config: LocalConfig) {
    const backend = config.backend;
    this.name = `local-${backend}`;

    if (backend === 'cloudflare-workers-ai') {
      const accountId = config.accountId ?? process.env.CF_ACCOUNT_ID;
      const apiToken = config.apiToken ?? process.env.CF_API_TOKEN;
      if (!accountId || !apiToken) {
        throw new Error('CF Workers AI requires accountId and apiToken');
      }
      const baseUrl = config.baseUrl
        ?? `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/v1`;
      this.healthUrl = `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/models`;
      this.inner = new OpenAICompatProvider({
        name: this.name,
        baseUrl,
        apiKey: apiToken,
        defaultModel: config.defaultModel ?? '@cf/meta/llama-3.1-8b-instruct',
      });
    } else if (backend === 'mlx') {
      // MLX (Apple Silicon optimized — preferred)
      const baseUrl = config.baseUrl ?? process.env.LOCAL_LLM_URL ?? 'http://localhost:11435';
      this.healthUrl = baseUrl.endsWith('/v1') ? `${baseUrl}/models` : `${baseUrl}/v1/models`;
      this.inner = new OpenAICompatProvider({
        name: this.name,
        baseUrl: baseUrl.endsWith('/v1') ? baseUrl : `${baseUrl}/v1`,
        apiKey: process.env.LLM_API_KEY ?? 'mlx',
        defaultModel: config.defaultModel ?? 'mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit',
      });
    } else {
      // Ollama (cross-platform fallback)
      const baseUrl = config.baseUrl ?? 'http://localhost:11434';
      this.healthUrl = baseUrl.endsWith('/v1') ? `${baseUrl}/models` : `${baseUrl}/v1/models`;
      this.inner = new OpenAICompatProvider({
        name: this.name,
        baseUrl: baseUrl.endsWith('/v1') ? baseUrl : `${baseUrl}/v1`,
        apiKey: 'ollama',
        defaultModel: config.defaultModel ?? 'llama3.2',
      });
    }
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.inner.chat(request);
    return { ...response, cost: 0, provider: this.name };
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(this.healthUrl, {
        signal: AbortSignal.timeout(3000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    return this.inner.listModels();
  }
}
