/**
 * OpenAI provider — convenience wrapper with OpenAI-specific defaults.
 * Delegates to OpenAICompatProvider with proper defaults.
 */
import { OpenAICompatProvider } from './openai-compatible.js';
import type { ChatRequest, ChatResponse, LlmProvider } from '../types.js';

export interface OpenAIConfig {
  apiKey: string;
  baseUrl?: string;
  defaultModel?: string;
  organization?: string;
}

export class OpenAIProvider implements LlmProvider {
  readonly name = 'openai';
  private inner: OpenAICompatProvider;
  private organization?: string;

  constructor(config: OpenAIConfig) {
    this.organization = config.organization;
    this.inner = new OpenAICompatProvider({
      name: 'openai',
      baseUrl: config.baseUrl ?? 'https://api.openai.com/v1',
      apiKey: config.apiKey,
      defaultModel: config.defaultModel ?? 'gpt-4o',
    });
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.inner.chat(request);
  }

  async isAvailable(): Promise<boolean> {
    return this.inner.isAvailable();
  }

  async listModels(): Promise<string[]> {
    return this.inner.listModels();
  }
}
