/**
 * Context Visualizer type definitions — tokens, compression events, metrics.
 */

export interface TokenUsage {
  /** Tokens consumed by system prompt */
  systemPrompt: number;
  /** Tokens from CLAUDE.md / project context */
  claudeMd: number;
  /** Tokens from conversation history */
  conversation: number;
  /** Tokens from tool results */
  toolResults: number;
  /** Total context window */
  total: number;
}

export interface CompressionEvent {
  id: string;
  /** Timestamp offset in seconds from session start */
  offsetSec: number;
  /** Tokens before compression */
  tokensBefore: number;
  /** Tokens after compression */
  tokensAfter: number;
  /** Compression ratio 0-1 (tokensAfter / tokensBefore) */
  ratio: number;
  /** Type of compression applied */
  type: "compact" | "prune" | "reset";
}

export interface ContextMetrics {
  tokenUsage: TokenUsage;
  compressionEvents: CompressionEvent[];
  /** Number of cache hits this session */
  cacheHits: number;
  /** Average latency across all tool calls (ms) */
  avgLatencyMs: number;
  /** Estimated session cost in USD */
  estimatedCostUsd: number;
  /** Session duration in seconds */
  sessionDurationSec: number;
}
