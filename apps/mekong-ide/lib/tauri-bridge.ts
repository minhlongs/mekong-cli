/**
 * tauri-bridge.ts
 * TypeScript bindings for the Tauri IPC layer.
 * All functions are no-ops (or throw) when running in a browser outside Tauri.
 */
import { invoke } from "@tauri-apps/api/core";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface EngineStatus {
  online: boolean;
  models: string[];
  port: number;
}

export interface LlmHealthResponse {
  mlx: EngineStatus;
  ollama: EngineStatus;
}

export interface GatewayHealth {
  online: boolean;
  version: string | null;
  timestamp: string | null;
}

export interface FileEntry {
  name: string;
  path: string;
  is_dir: boolean;
  size: number;
}

export interface SystemInfo {
  cpu_arch: string;
  os: string;
  memory_total_gb: number;
  hostname: string;
}

// ── Guard ─────────────────────────────────────────────────────────────────────

/** Returns true when running inside a Tauri webview.
 * Uses __TAURI_INTERNALS__ (v2) and dynamic property access
 * to prevent Next.js tree-shaking from eliminating Tauri code paths.
 */
export function isTauri(): boolean {
  try {
    return typeof window !== "undefined" &&
      "__TAURI_INTERNALS__" in window;
  } catch (_) {
    return false;
  }
}

// ── LLM commands ─────────────────────────────────────────────────────────────

/** Probe MLX (:11435) and Ollama (:11434) health. */
export async function checkLlmHealth(): Promise<LlmHealthResponse> {
  return invoke<LlmHealthResponse>("check_llm_health");
}

/** Check local gateway health at :8000. */
export async function checkGatewayHealth(): Promise<GatewayHealth> {
  return invoke<GatewayHealth>("check_gateway_health");
}

/**
 * Send a single-turn chat message to the specified model.
 * MLX is tried first; Ollama is the fallback.
 */
export async function chatCompletion(
  model: string,
  message: string
): Promise<string> {
  return invoke<string>("chat_completion", { model, message });
}

// ── Gateway commands ──────────────────────────────────────────────────────────

/** List tenants from the local gateway (:8000). */
export async function listTenants(): Promise<unknown[]> {
  return invoke<unknown[]>("list_tenants");
}

// ── Filesystem commands ───────────────────────────────────────────────────────

/** List non-hidden files/dirs in the given workspace path. */
export async function readWorkspace(path: string): Promise<FileEntry[]> {
  return invoke<FileEntry[]>("read_workspace", { path });
}

/** Read a UTF-8 text file. */
export async function readFile(path: string): Promise<string> {
  return invoke<string>("read_file", { path });
}

// ── System commands ───────────────────────────────────────────────────────────

/** Return host system information (OS, arch, memory, hostname). */
export async function getSystemInfo(): Promise<SystemInfo> {
  return invoke<SystemInfo>("get_system_info");
}
