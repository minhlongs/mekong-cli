/**
 * MekongEngine Adapter - Bridges MekongEngine from @mekong/cli-core with Cloudflare Workers environment
 *
 * Since MekongEngine is designed for Node.js runtime, this adapter provides a Workers-compatible
 * interface by mapping Cloudflare Bindings to MekongEngine options.
 */

import type { Bindings } from '../index'
import type { Ai, AiModels } from '@cloudflare/workers-types'

export class MekongEngineAdapter {
  private aiBinding?: Ai
  private llmApiKey?: string
  private llmBaseUrl?: string
  private model: string

  constructor(bindings: Bindings) {
    this.aiBinding = bindings.AI
    this.llmApiKey = bindings.LLM_API_KEY
    this.llmBaseUrl = bindings.LLM_BASE_URL
    this.model = bindings.DEFAULT_LLM_MODEL || '@cf/meta/llama-3.1-8b-instruct'
  }

  /**
   * Initialize the adapter (placeholder for future MekongEngine integration)
   * Currently provides direct Workers AI access while maintaining MekongEngine interface
   */
  async init(): Promise<void> {
    // Future: Initialize MekongEngine with Workers-compatible config
    // For now, adapter serves as abstraction layer for LLM access
  }

  /**
   * Run a goal through the engine
   * Uses Workers AI directly when MekongEngine is not Workers-compatible
   */
  async run(goal: string): Promise<{ output: string; status: 'success' | 'partial' | 'failed' }> {
    if (!this.aiBinding && !this.llmApiKey) {
      return {
        output: 'Error: No LLM provider configured (need AI binding or LLM_API_KEY)',
        status: 'failed',
      }
    }

    try {
      // Use Workers AI if available, otherwise fall back to external LLM
      if (this.aiBinding) {
        const result = await this.aiBinding.run(this.model as keyof AiModels, {
          messages: [
            { role: 'system', content: 'You are a helpful assistant. Respond concisely.' },
            { role: 'user', content: goal },
          ],
          max_tokens: 2000,
        })
        return {
          output: (result as { response?: string }).response || 'No response from AI',
          status: 'success',
        }
      }

      // Fallback to external LLM via fetch
      if (this.llmApiKey && this.llmBaseUrl) {
        const response = await fetch(`${this.llmBaseUrl}/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${this.llmApiKey}`,
          },
          body: JSON.stringify({
            model: this.model.replace('@cf/meta/', ''),
            messages: [
              { role: 'system', content: 'You are a helpful assistant.' },
              { role: 'user', content: goal },
            ],
            max_tokens: 2000,
          }),
        })

        if (!response.ok) {
          throw new Error(`LLM API error: ${response.status}`)
        }

        const data = (await response.json()) as { choices?: Array<{ message?: { content?: string } }> }
        return {
          output: data.choices?.[0]?.message?.content || 'No response from AI',
          status: 'success',
        }
      }

      return {
        output: 'Error: No LLM provider available',
        status: 'failed',
      }
    } catch (error) {
      return {
        output: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        status: 'failed',
      }
    }
  }

  /**
   * Get adapter status
   */
  getStatus(): {
    hasAiBinding: boolean
    hasLlmApiKey: boolean
    model: string
    initialized: boolean
  } {
    return {
      hasAiBinding: !!this.aiBinding,
      hasLlmApiKey: !!this.llmApiKey,
      model: this.model,
      initialized: true,
    }
  }
}
