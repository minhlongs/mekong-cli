/**
 * Type declarations for @openclaw/engine modules
 * These modules are JavaScript-only, this file provides TypeScript types
 */

declare module '@openclaw/engine/raas/raas-api.js' {
  export function handleValidate(
    tenantId: string,
    command: string,
    cost: number
  ): { ok: boolean; data?: { remainingCredits: number }; error?: string };

  export function handleGetBalance(
    tenantId: string
  ): {
    ok: boolean;
    data?: {
      tier: string;
      used: number;
      limit: number;
      remaining: number;
    };
    error?: string;
  };

  export function handleListTiers(): {
    ok: boolean;
    data?: Record<
      string,
      { priceUsd: number; creditsPerMonth: number; maxProjects: number }
    >;
  };

  export function handleRegisterTenant(config: {
    tenantId: string;
    tier: 'starter' | 'pro' | 'enterprise';
    active: boolean;
    expiresAt: number;
    usedCredits: number;
  }): { ok: boolean; error?: string };

  export function handleGetUsage(tenantId: string): {
    ok: boolean;
    data?: unknown;
    error?: string;
  };
}

declare module '@openclaw/engine/raas/raas-onboarding.js' {
  export function handleOnboardTenant(config: {
    tenantId: string;
    tier: 'starter' | 'pro' | 'enterprise';
    email: string;
  }): {
    ok: boolean;
    data?: {
      apiKey: string;
      creditsPerMonth: number;
      expiresAt: number;
      tenantId: string;
      tier: string;
    };
    error?: string;
  };

  export function validateApiKey(apiKey: string): {
    ok: boolean;
    data?: { tenantId: string; tier: string };
    error?: string;
  };

  export function revokeApiKey(apiKey: string): {
    ok: boolean;
    error?: string;
  };
}

declare module '@openclaw/engine/raas/raas-billing' {
  export function getUsageAnalytics(tenantId: string): {
    ok: boolean;
    data?: {
      totalCalls: number;
      successfulCalls: number;
      throttledCount: number;
      avgLatencyMs: number;
    };
    error?: string;
  };
}

declare module '@openclaw/engine/raas/raas-rate-limiter' {
  export function getRateLimitStatus(
    tenantId: string,
    tier: string
  ): {
    tokens: number;
    maxTokens: number;
  };
}

declare module '@openclaw/engine/raas/raas-health' {
  export function checkHealth(): {
    ok: boolean;
    data?: {
      status: string;
      version: string;
      uptime: number;
      components: Array<{
        name: string;
        status: string;
        message?: string;
      }>;
    };
    error?: string;
  };
}

declare module '@openclaw/engine/orchestration/auto-cto-pilot' {
  export function getCtoStatus(): {
    phase: string;
    currentProjectIdx: number;
    cycle: number;
    errorCount: number;
    fixIndex: number;
    totalPanes: number;
    cooldownMs: number;
    priorities: Record<string, number>;
  };

  export function resetCtoState(): {
    phase: string;
    currentProjectIdx: number;
    cycle: number;
  };
}
