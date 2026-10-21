/**
 * LLM Client Types & Circuit Breaker Health Tracker
 */

import { z } from 'zod'

export const LLMResponseSchema = z.object({
  content: z.string(),
  model: z.string(),
  usage: z.record(z.number()).optional(),
})

export type LLMResponse = z.infer<typeof LLMResponseSchema>

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatOptions {
  model?: string
  temperature?: number
  max_tokens?: number
  json_mode?: boolean
}

export interface ProviderHealth {
  failures: number
  lastFailure: number
  cooldownMs: number
}

export interface LLMProvider {
  name: string
  baseUrl: string
  apiKey: string
  isAvailable(): boolean
}

export function filterHealthyProviders(
  providers: LLMProvider[],
  health: Map<string, ProviderHealth>
): LLMProvider[] {
  const now = Date.now()
  return providers.filter((p) => {
    if (p.name === 'offline') return true
    const h = health.get(p.name)
    if (!h) return true
    if (h.failures < 3) return true
    return now - h.lastFailure > h.cooldownMs
  })
}

export function recordProviderFailure(
  health: Map<string, ProviderHealth>,
  name: string
): void {
  const h = health.get(name) ?? { failures: 0, lastFailure: 0, cooldownMs: 60_000 }
  h.failures++
  h.lastFailure = Date.now()
  health.set(name, h)
}

export function recordProviderSuccess(
  health: Map<string, ProviderHealth>,
  name: string
): void {
  const h = health.get(name)
  if (h) h.failures = 0
}

export function buildOfflineResponse(messages: ChatMessage[], error: string): LLMResponse {
  const userMsg = [...messages].reverse().find((m) => m.role === 'user')?.content ?? ''
  return {
    content: `[OFFLINE] LLM unavailable (${error}). Request: ${userMsg.slice(0, 200)}`,
    model: 'offline',
  }
}
