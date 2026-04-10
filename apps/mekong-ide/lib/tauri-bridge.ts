/**
 * tauri-bridge.ts — Tauri IPC bindings via window.__TAURI_INTERNALS__
 * No @tauri-apps/api import — prevents SSR build failures.
 */
/* eslint-disable @typescript-eslint/no-explicit-any */

export interface EngineStatus { online: boolean; models: string[]; port: number; }
export interface LlmHealthResponse { mlx: EngineStatus; ollama: EngineStatus; }
export interface GatewayHealth { online: boolean; version: string | null; timestamp: string | null; }
export interface FileEntry { name: string; path: string; is_dir: boolean; size: number; }
export interface SystemInfo { cpu_arch: string; os: string; memory_total_gb: number; hostname: string; }

export function isTauri(): boolean {
  try { return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window; }
  catch (_) { return false; }
}

async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const fn = (globalThis as any).__TAURI_INTERNALS__?.invoke;
  if (!fn) throw new Error("Tauri not available");
  return fn(cmd, args);
}

export async function checkLlmHealth() { return invoke<LlmHealthResponse>("check_llm_health"); }
export async function checkGatewayHealth() { return invoke<GatewayHealth>("check_gateway_health"); }
export async function chatCompletion(model: string, message: string) { return invoke<string>("chat_completion", { model, message }); }
export async function listTenants() { return invoke<unknown[]>("list_tenants"); }
export async function readWorkspace(path: string) { return invoke<FileEntry[]>("read_workspace", { path }); }
export async function readFile(path: string) { return invoke<string>("read_file", { path }); }
export async function getSystemInfo() { return invoke<SystemInfo>("get_system_info"); }
