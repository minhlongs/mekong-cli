/**
 * Mekong CLI — Environment Configuration for Ollama MLX Engine.
 *
 * Centralized env resolution for local Ollama inference.
 * Ollama 0.19+ uses Apple MLX natively on Apple Silicon.
 *
 * Strategy (100/100 model stack):
 *   DEV:  qwen3:30b-a3b (18GB MoE) + deepseek-r1:32b (19GB) = 38.7GB
 *   PROD: qwen2.5-coder:7b + qwen3:8b = 14.7GB (B2B lightweight)
 *   Shared: qwen3:1.7b (tool), phi4-mini-reasoning (trading),
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
  default: 'qwen3:30b-a3b',
  reasoning: 'deepseek-r1:32b',
  tool: 'qwen3:1.7b',
  trading: 'phi4-mini-reasoning',
  embed: 'nomic-embed-text',
} as const

const PROD_MODELS = {
  default: 'qwen2.5-coder:7b',
  reasoning: 'qwen3:8b',
  tool: 'qwen3:1.7b',
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
    baseUrl: process.env.OPENAI_BASE_URL ?? 'http://127.0.0.1:11434/v1',
    apiKey: process.env.OPENAI_API_KEY ?? 'ollama',
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
  process.env.OPENAI_BASE_URL ??= 'http://127.0.0.1:11434/v1'
  process.env.OPENAI_API_KEY ??= 'ollama'
  process.env.OPENAI_MODEL ??= getDefaultModel()
}
