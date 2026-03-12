import { NextResponse } from 'next/server'
import type { LLMRequest, LLMResponse } from '../../lib/llm-types'

const OLLAMA_BASE_URL = process.env.LLM_BASE_URL || 'http://localhost:11434'
const DEFAULT_MODEL = process.env.LLM_MODEL || 'llama3.2:3b'

/**
 * POST /api/generate
 * Generate text using local Ollama LLM
 */
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const {
      prompt,
      model = DEFAULT_MODEL,
      maxTokens,
      temperature,
    } = body as LLMRequest

    // Validation
    if (!prompt || prompt.trim().length === 0) {
      return NextResponse.json(
        { error: 'Invalid request', message: 'Prompt is required' },
        { status: 400 }
      )
    }

    if (prompt.length > 4000) {
      return NextResponse.json(
        { error: 'Invalid request', message: 'Prompt too long (max 4000 chars)' },
        { status: 400 }
      )
    }

    // Call Ollama API
    const ollamaResponse = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        prompt: prompt.trim(),
        stream: false,
        options: {
          num_predict: maxTokens || 512,
          temperature: temperature ?? 0.7,
        },
      }),
    })

    if (!ollamaResponse.ok) {
      await ollamaResponse.text() // Consume response body
      // Log error for debugging (removed in production via compiler config)
      return NextResponse.json(
        { error: 'LLM error', message: 'Failed to generate response' },
        { status: 500 }
      )
    }

    const data = await ollamaResponse.json() as LLMResponse

    return NextResponse.json({
      response: data.response,
      model,
      done: data.done,
    })
  } catch {
    // Error handling (removed in production via compiler config)
    return NextResponse.json(
      { error: 'Server error', message: 'Internal server error' },
      { status: 500 }
    )
  }
}
