/**
 * Mock data for Context Visualizer.
 */
import type { ContextMetrics } from "@/lib/types/context-types";

export const MOCK_CONTEXT: ContextMetrics = {
  tokenUsage: {
    systemPrompt: 4200,
    claudeMd:     8900,
    conversation: 38400,
    toolResults:  10600,
    total:        100000,
  },
  compressionEvents: [
    { id: "c1", offsetSec: 120,  tokensBefore: 42000, tokensAfter: 28000, ratio: 0.67, type: "compact" },
    { id: "c2", offsetSec: 480,  tokensBefore: 71000, tokensAfter: 44000, ratio: 0.62, type: "prune"   },
    { id: "c3", offsetSec: 810,  tokensBefore: 89000, tokensAfter: 52000, ratio: 0.58, type: "compact" },
    { id: "c4", offsetSec: 1140, tokensBefore: 95000, tokensAfter: 38000, ratio: 0.40, type: "reset"   },
  ],
  cacheHits:         14,
  avgLatencyMs:      340,
  estimatedCostUsd:  0.04,
  sessionDurationSec: 1800,
};
