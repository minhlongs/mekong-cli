/**
 * Mock data for Engine Farm Monitor — 3 engines + system resources.
 */
import type { Engine, SystemResources } from "@/lib/types/engine-types";

export const MOCK_ENGINES: Engine[] = [
  {
    id: "mlx-qwen",
    name: "MLX Local",
    model: "Qwen2.5-Coder-32B",
    provider: "mlx",
    status: "running",
    port: 8080,
    resources: { ram: 72, gpu: 64, vram: 78 },
    tokensPerSec: 42,
    latencyMs: 230,
  },
  {
    id: "ollama-deepseek",
    name: "Ollama",
    model: "DeepSeek-R1-32B",
    provider: "ollama",
    status: "idle",
    port: 11434,
    resources: { ram: 38, gpu: 12, vram: 45 },
    tokensPerSec: 0,
    latencyMs: 180,
  },
  {
    id: "mlx-gemma",
    name: "MLX Vision",
    model: "Gemma-4-26B",
    provider: "mlx",
    status: "stopped",
    port: 8081,
    resources: { ram: 0, gpu: 0, vram: 0 },
    tokensPerSec: 0,
    latencyMs: 0,
  },
];

export const MOCK_SYSTEM: SystemResources = {
  totalRam: 128,
  usedRam: 93,
  gpuUtilization: 58,
  ramSegments: [
    { engineId: "mlx-qwen",      engineName: "MLX Local",   percent: 36, color: "var(--accent-teal-500)" },
    { engineId: "ollama-deepseek", engineName: "Ollama",    percent: 19, color: "var(--model-reasoning)" },
    { engineId: "mlx-gemma",     engineName: "MLX Vision",  percent: 13, color: "var(--model-architect)" },
  ],
};

export const MOCK_QUEUE = { pending: 7, active: 3, failed: 1 };
export const MOCK_ROUTER = { routed: 284, avgRouteMs: 12, fallbacks: 3 };
