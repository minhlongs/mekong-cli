/**
 * Engine Farm type definitions — engine status, resource usage, config.
 */

export type EngineStatus = "running" | "idle" | "stopped" | "error";
export type EngineProvider = "mlx" | "ollama" | "anthropic" | "openai";

export interface ResourceUsage {
  /** RAM utilization 0-100 */
  ram: number;
  /** GPU utilization 0-100 */
  gpu: number;
  /** VRAM utilization 0-100 */
  vram: number;
}

export interface Engine {
  id: string;
  name: string;
  model: string;
  provider: EngineProvider;
  status: EngineStatus;
  port: number;
  resources: ResourceUsage;
  /** Tokens per second (0 when idle/stopped) */
  tokensPerSec: number;
  /** Avg latency in ms (0 when stopped) */
  latencyMs: number;
}

export interface SystemResources {
  totalRam: number;
  usedRam: number;
  gpuUtilization: number;
  /** Segments: which engine uses what % of RAM */
  ramSegments: Array<{ engineId: string; engineName: string; percent: number; color: string }>;
}
