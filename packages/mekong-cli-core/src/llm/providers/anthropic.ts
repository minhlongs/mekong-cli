/**
 * Anthropic provider — native Claude Messages API.
 * Uses fetch directly (no SDK dependency for portability).
 */
import type { ChatRequest, ChatResponse, LlmProvider } from '../types.js';

export interface AnthropicConfig {
  apiKey: string;
  baseUrl?: string;
  defaultModel?: string;
  apiVersion?: string;
}

export class AnthropicProvider implements LlmProvider {
  readonly name = 'anthropic';
  private apiKey: string;
  private baseUrl: string;
  private defaultModel: string;
  private apiVersion: string;

  constructor(config: AnthropicConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl ?? 'https://api.anthropic.com').replace(/\/+$/, '');
    this.defaultModel = config.defaultModel ?? 'claude-sonnet-4-20250514';
    this.apiVersion = config.apiVersion ?? '2023-06-01';
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    const model = request.model ?? this.defaultModel;
    const startTime = Date.now();

    const body: Record<string, unknown> = {
      model,
      max_tokens: request.maxTokens ?? 4096,
      messages: this.formatMessages(request),
    };

    if (request.systemPrompt) {
      body.system = request.systemPrompt;
    }
    if (request.temperature !== undefined) {
      body.temperature = request.temperature;
    }
    if (request.tools?.length) {
      body.tools = request.tools.map(t => ({
        name: t.name,
        description: t.description,
        input_schema: t.parameters,
      }));
    }

    const response = await fetch(`${this.baseUrl}/v1/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': this.apiKey,
        'anthropic-version': this.apiVersion,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Anthropic API error (${response.status}): ${errorText}`);
    }

    const data = await response.json() as AnthropicResponse;
    const latencyMs = Date.now() - startTime;

    const textContent = data.content
      ?.filter(b => b.type === 'text')
      .map(b => b.text)
      .join('') ?? '';

    const toolUses = data.content
      ?.filter(b => b.type === 'tool_use')
      .map(b => ({
        id: b.id!,
        name: b.name!,
        arguments: (b.input as Record<string, unknown>) ?? {},
      }));

    return {
      content: textContent,
      toolCalls: toolUses?.length ? toolUses : undefined,
      usage: {
        inputTokens: data.usage?.input_tokens ?? 0,
        outputTokens: data.usage?.output_tokens ?? 0,
      },
      cost: 0, // calculated by CostTracker
      model,
      provider: 'anthropic',
      latencyMs,
      finishReason: mapStopReason(data.stop_reason),
    };
  }

  async isAvailable(): Promise<boolean> {
    return Boolean(this.apiKey);
  }

  private formatMessages(request: ChatRequest): AnthropicMessage[] {
    const messages: AnthropicMessage[] = [];
    for (const msg of request.messages) {
      if (msg.role === 'system') continue; // handled via body.system
      messages.push({
        role: msg.role === 'assistant' ? 'assistant' : 'user',
        content: msg.content,
      });
    }
    return messages;
  }
}

function mapStopReason(reason?: string): ChatResponse['finishReason'] {
  switch (reason) {
    case 'end_turn': return 'stop';
    case 'tool_use': return 'tool_calls';
    case 'max_tokens': return 'length';
    default: return 'stop';
  }
}

interface AnthropicMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface AnthropicResponse {
  content?: Array<{
    type: 'text' | 'tool_use';
    text?: string;
    id?: string;
    name?: string;
    input?: unknown;
  }>;
  stop_reason?: string;
  usage?: { input_tokens?: number; output_tokens?: number };
}
