/**
 * Local LLM provider — supports MLX, Ollama, and any OpenAI-compatible server.
 * MLX is preferred on Apple Silicon for optimal performance.
 */
import { OpenAICompatProvider } from './openai-compatible.js';
import type { LlmProvider, ChatRequest, ChatResponse } from '../types.js';

export class LocalLLMProvider implements LlmProvider {
  readonly name = 'local-llm';
  private inner: OpenAICompatProvider;
  private baseUrl: string;

  constructor(baseUrl?: string, defaultModel?: string) {
    this.baseUrl = baseUrl ?? process.env.LOCAL_LLM_URL ?? 'http://localhost:11435';
    this.inner = new OpenAICompatProvider({
      name: 'local-llm',
      baseUrl: this.baseUrl.endsWith('/v1') ? this.baseUrl : `${this.baseUrl}/v1`,
      apiKey: process.env.LLM_API_KEY ?? 'mlx',
      defaultModel: defaultModel ?? process.env.LOCAL_LLM_MODEL ?? 'mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit',
    });
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.inner.chat(request);
    return { ...response, cost: 0, provider: 'local-llm' }; // Local = free
  }

  async isAvailable(): Promise<boolean> {
    try {
      const url = this.baseUrl.endsWith('/v1')
        ? `${this.baseUrl}/models`
        : `${this.baseUrl}/v1/models`;
      const response = await fetch(url, { signal: AbortSignal.timeout(3000) });
      return response.ok;
    } catch {
      return false;
    }
  }

  async listModels(): Promise<string[]> {
    try {
      const url = this.baseUrl.endsWith('/v1')
        ? `${this.baseUrl}/models`
        : `${this.baseUrl}/v1/models`;
      const response = await fetch(url);
      if (!response.ok) return [];
      const data = await response.json() as { data?: Array<{ id: string }> };
      return data.data?.map(m => m.id) ?? [];
    } catch {
      return [];
    }
  }
}

// Backward compatibility
export const OllamaProvider = LocalLLMProvider;
