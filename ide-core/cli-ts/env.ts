/**
 * Mekong CLI — Environment Configuration for Rapid-MLX Engine.
 *
 * Centralized env resolution for local Rapid-MLX inference.
 * Rapid-MLX uses Apple MLX natively on Apple Silicon — 4.2x faster than Ollama.
 *
 * Strategy (Qwen 3.6-35B primary):
 *   DEV:  qwen3.6-35b (20GB MoE, 262K context) — primary model
 *   PROD: qwen3.6-35b (lightweight via Rapid-MLX)
 *   Shared: qwen3.5-4b (tool), phi4-mini-reasoning (trading),
 *   nomic-embed-text (embeddings)
 */

export type MekongEnv = 'development' | 'production'

export interface OllamaConfig {
  baseUrl: string
  apiKey: string
  defaultModel: string
  reasoningModel: string
  toolModel: string
  tradingModel: string
  embedModel: string
  env: MekongEnv
}

const DEV_MODELS = {
  default: 'qwen3.6-35b',
  reasoning: 'qwen3.6-35b',
  tool: 'qwen3.5-4b',
  trading: 'phi4-mini-reasoning',
  embed: 'nomic-embed-text',
} as const

const PROD_MODELS = {
  default: 'qwen3.6-35b',
  reasoning: 'qwen3.6-35b',
  tool: 'qwen3.5-4b',
  trading: 'phi4-mini-reasoning',
  embed: 'nomic-embed-text',
} as const

/**
 * Resolve the current Mekong environment.
 */
export function getMekongEnv(): MekongEnv {
  const env = process.env.MEKONG_ENV
  return env === 'production' ? 'production' : 'development'
}

/**
 * Get the default model for the current environment.
 */
export function getDefaultModel(): string {
  return process.env.OPENAI_MODEL
    ?? (getMekongEnv() === 'production'
      ? PROD_MODELS.default
      : DEV_MODELS.default)
}

/**
 * Build full Ollama configuration from environment.
 */
export function getOllamaConfig(): OllamaConfig {
  const env = getMekongEnv()
  const models = env === 'production' ? PROD_MODELS : DEV_MODELS

  return {
    baseUrl: process.env.OPENAI_BASE_URL ?? 'http://127.0.0.1:8001/v1',
    apiKey: process.env.OPENAI_API_KEY ?? 'mlx',
    defaultModel: process.env.OPENAI_MODEL ?? models.default,
    reasoningModel: models.reasoning,
    toolModel: models.tool,
    tradingModel: models.trading,
    embedModel: models.embed,
    env,
  }
}

/**
 * Apply Ollama environment variables for OpenAI-compatible mode.
 * Call this early in CLI bootstrap to ensure all downstream code
 * uses the local Ollama endpoint.
 *
 * Only sets vars that are NOT already defined — explicit env wins.
 */
export function applyOllamaEnv(): void {
  process.env.CLAUDE_CODE_USE_OPENAI ??= '1'
  process.env.OPENAI_BASE_URL ??= 'http://127.0.0.1:8001/v1'
  process.env.OPENAI_API_KEY ??= 'mlx'
  process.env.OPENAI_MODEL ??= getDefaultModel()
}
