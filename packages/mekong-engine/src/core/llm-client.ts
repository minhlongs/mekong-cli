/**
 * LLM Client — OpenAI-compatible with circuit breaker failover.
 * Mirrors Python: src/core/llm_client.py
 *
 * Runs natively on CF Workers using fetch() — no SDK deps needed.
 */

import type { Ai } from '@cloudflare/workers-types'
import {
  LLMResponseSchema,
  type LLMResponse,
  type ChatMessage,
  type ChatOptions,
  type ProviderHealth,
  type LLMProvider,
  filterHealthyProviders,
  recordProviderFailure,
  recordProviderSuccess,
  buildOfflineResponse,
} from './llm-client-health'

export { LLMResponseSchema, type LLMResponse, type ChatMessage, type ChatOptions }

export class LLMClient {
  private providers: LLMProvider[]
  private health: Map<string, ProviderHealth> = new Map()
  private defaultModel: string
  private ai?: Ai

  constructor(opts: {
    ai?: Ai
    llmApiKey?: string
    llmBaseUrl?: string
    model?: string
  }) {
    this.defaultModel = opts.model ?? '@cf/meta/llama-3.1-8b-instruct'
    this.ai = opts.ai
    this.providers = []

    const baseUrl = opts.llmBaseUrl ?? 'https://api.openai.com/v1'
    const apiKey = opts.llmApiKey ?? ''

    if (apiKey) {
      this.providers.push({
        name: 'primary',
        baseUrl,
        apiKey,
        isAvailable: () => true,
      })
    }

    this.providers.push({
      name: 'offline',
      baseUrl: '',
      apiKey: '',
      isAvailable: () => true,
    })
  }

  get isAvailable(): boolean {
    if (this.ai && this.defaultModel.startsWith('@cf/')) return true
    return this.providers.some((p) => p.name !== 'offline' && p.isAvailable())
  }

  async chat(messages: ChatMessage[], opts: ChatOptions = {}): Promise<LLMResponse> {
    const model = opts.model ?? this.defaultModel
    const temperature = opts.temperature ?? 0.7
    const maxTokens = opts.max_tokens ?? 2048

    if (this.ai && model.startsWith('@cf/')) {
      try {
        const result = await this.ai.run(model as Parameters<Ai['run']>[0], {
          messages: messages.map((m) => ({ role: m.role, content: m.content })),
          max_tokens: maxTokens,
        })

        const text = (result as { response?: string })?.response ?? ''
        if (text) {
          const usage = (result as { usage?: Record<string, number> })?.usage
          return { content: text, model, usage }
        }
      } catch {
        // Fall through to HTTP providers
      }
    }

    for (const provider of filterHealthyProviders(this.providers, this.health)) {
      if (provider.name === 'offline') break

      try {
        const body: Record<string, unknown> = {
          model,
          messages,
          temperature,
          max_tokens: maxTokens,
        }
        if (opts.json_mode) {
          body.response_format = { type: 'json_object' }
        }

        const resp = await fetch(`${provider.baseUrl}/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${provider.apiKey}`,
          },
          body: JSON.stringify(body),
        })

        if (!resp.ok) {
          const errText = await resp.text()
          recordProviderFailure(this.health, provider.name)
          if (resp.status === 400) {
            return buildOfflineResponse(messages, `bad request: ${errText}`)
          }
          continue
        }

        const data = (await resp.json()) as {
          choices: Array<{ message: { content: string } }>
          model: string
          usage?: Record<string, number>
        }

        recordProviderSuccess(this.health, provider.name)

        return {
          content: data.choices[0]?.message?.content ?? '',
          model: data.model ?? model,
          usage: data.usage,
        }
      } catch {
        recordProviderFailure(this.health, provider.name)
        continue
      }
    }

    return buildOfflineResponse(messages, 'all providers failed')
  }

  async generate(prompt: string, opts: ChatOptions = {}): Promise<string> {
    const resp = await this.chat([{ role: 'user', content: prompt }], opts)
    return resp.content
  }

  async generateJson(prompt: string, opts: ChatOptions = {}): Promise<Record<string, unknown>> {
    const messages: ChatMessage[] = [
      { role: 'system', content: 'Always respond with valid JSON.' },
      { role: 'user', content: prompt },
    ]
    const resp = await this.chat(messages, { ...opts, json_mode: true })
    try {
      return JSON.parse(resp.content) as Record<string, unknown>
    } catch {
      return { raw_content: resp.content }
    }
  }
}
