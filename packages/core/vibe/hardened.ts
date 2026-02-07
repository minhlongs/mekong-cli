/**
 * 🛡️ VIBE Hardened - Production-Ready Patterns (Proxy)
 */
export * from './src/hardened/skeleton';
export * from './src/hardened/error-boundary';
export * from './src/hardened/shortcuts';
export * from './src/hardened/deployment';
export * from './src/hardened/diagnostics';
export * from './src/hardened/checklist';

import { ShortcutRegistry } from './src/hardened/shortcuts';

/** @deprecated Use src/hardened modules directly */
export const shortcuts = new ShortcutRegistry();

// Re-export isProductionReady function
export function isProductionReady(): boolean {
    // Simple production readiness check
    return process.env.NODE_ENV === 'production';
}
