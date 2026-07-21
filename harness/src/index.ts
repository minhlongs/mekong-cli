/**
 * @mekong/harness-core - Main Entry Point
 * Shared harness runtime for Mekong (mk) and Agent Kit (ak) personas
 */

// Core types
export * from './core/types.js';

// Config & Session
export { ConfigManager } from './core/config-manager.js';
export { SessionManager } from './core/session-manager.js';
export { HookEngine } from './core/hook-engine.js';
export { CommandRouter } from './core/command-router.js';

// Memory
export { MemoryLayerImpl } from './memory/memory-layer.js';

// LLM
export { LLMRouter, PROVIDER_PRESETS, createEndpointFromPreset } from './providers/llm-router.js';

// Personas
export { MekongPersona, AgentKitPersona, getPersonaConfig, detectPersona, routeCommand } from './personas/personas.js';
// export type { PersonaConfig } from './personas/personas.js'; // Already exported from core/types