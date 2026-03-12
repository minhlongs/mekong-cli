/**
 * Local provider — supports Ollama and Cloudflare Workers AI.
 * Auto-detects which local endpoint is available.
 */
import { OpenAICompatProvider } from './openai-compatible.js';
import type { ChatRequest, ChatResponse, LlmProvider } from '../types.js';

export interface LocalConfig {
  /** 'ollama' or 'cloudflare-workers-ai' */
  backend: 'ollama' | 'cloudflare-workers-ai';
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
    } else {
      // Ollama (default)
      const baseUrl = config.baseUrl ?? 'http://localhost:11434';
      this.healthUrl = baseUrl;
      this.inner = new OpenAICompatProvider({
        name: this.name,
        baseUrl: `${baseUrl}/v1`,
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
