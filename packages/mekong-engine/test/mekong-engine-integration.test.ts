import { describe, it, expect, beforeEach } from 'vitest'
import type { Ai } from '@cloudflare/workers-types'
import { MekongEngineAdapter } from '../src/core/mekong-engine-adapter'

describe('MekongEngine Integration', () => {
  const mockBindings = {
    AI: { run: async () => ({ response: 'Hello from mock AI' }) } as unknown as Ai,
    DEFAULT_LLM_MODEL: '@cf/meta/llama-3.1-8b-instruct',
  }

  describe('Import', () => {
    it('can import MekongEngineAdapter', async () => {
      const { MekongEngineAdapter } = await import('../src/core/mekong-engine-adapter')
      expect(MekongEngineAdapter).toBeDefined()
    })
  })

  describe('Instantiation', () => {
    it('can instantiate adapter with bindings', () => {
      const adapter = new MekongEngineAdapter(mockBindings)
      expect(adapter).toBeDefined()
    })

    it('initializes with default model when not provided', () => {
      const adapter = new MekongEngineAdapter({})
      const status = adapter.getStatus()
      expect(status.model).toBe('@cf/meta/llama-3.1-8b-instruct')
    })

    it('uses custom model when provided', () => {
      const adapter = new MekongEngineAdapter({
        DEFAULT_LLM_MODEL: '@cf/microsoft/phi-2',
      })
      const status = adapter.getStatus()
      expect(status.model).toBe('@cf/microsoft/phi-2')
    })
  })

  describe('Init', () => {
    it('can call init() without errors', async () => {
      const adapter = new MekongEngineAdapter(mockBindings)
      await expect(adapter.init()).resolves.not.toThrow()
    })
  })

  describe('Run with AI Binding', () => {
    beforeEach(() => {
      // Clear mocks before each test
    })

    it('can run a simple task through adapter with AI binding', async () => {
      const adapter = new MekongEngineAdapter(mockBindings)
      const result = await adapter.run('Say hello in one word')

      expect(result).toBeDefined()
      expect(result.status).toBe('success')
      expect(result.output).toBe('Hello from mock AI')
    })

    it('handles goal with complex content', async () => {
      const mockAI = {
        run: async () => ({ response: 'Complex response with multiple sentences.' })
      } as unknown as Ai

      const adapter = new MekongEngineAdapter({
        AI: mockAI,
        DEFAULT_LLM_MODEL: '@cf/meta/llama-3.1-8b-instruct',
      })

      const result = await adapter.run('Write a detailed plan for launching a SaaS product')

      expect(result.status).toBe('success')
      expect(result.output).toContain('Complex response')
    })
  })

  describe('Run without AI Binding', () => {
    it('returns error when no LLM provider configured', async () => {
      const adapter = new MekongEngineAdapter({})
      const result = await adapter.run('Test goal')

      expect(result.status).toBe('failed')
      expect(result.output).toContain('No LLM provider configured')
    })

    it('works with external LLM API key', async () => {
      const adapter = new MekongEngineAdapter({
        LLM_API_KEY: 'test-key',
        LLM_BASE_URL: 'https://api.openai.com/v1',
        DEFAULT_LLM_MODEL: 'gpt-3.5-turbo',
      })

      // This will fail in test environment (no real API), but tests the code path
      const result = await adapter.run('Test goal')

      // Expected to fail because we're using a fake API key
      expect(result.status).toBe('failed')
      expect(result.output).toContain('Error')
    })
  })

  describe('GetStatus', () => {
    it('returns correct status with AI binding', () => {
      const adapter = new MekongEngineAdapter(mockBindings)
      const status = adapter.getStatus()

      expect(status.hasAiBinding).toBe(true)
      expect(status.hasLlmApiKey).toBe(false)
      expect(status.initialized).toBe(true)
    })

    it('returns correct status with LLM API key', () => {
      const adapter = new MekongEngineAdapter({
        LLM_API_KEY: 'test-key',
      })
      const status = adapter.getStatus()

      expect(status.hasAiBinding).toBe(false)
      expect(status.hasLlmApiKey).toBe(true)
    })
  })
})
