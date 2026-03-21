/**
 * Onboarding V2 — internal helpers (step navigation, parsing, event logging)
 * Not exported as public API — used only by onboarding-v2-service.ts
 */

import type { D1Database } from '@cloudflare/workers-types';
import { ONBOARDING_STEPS, type OnboardingFlow } from './onboarding-v2-service';

/** Determine next incomplete step after `current` */
export function nextStep(
  current: string,
  completed: string[],
  skipped: string[],
): string | null {
  const done = new Set([...completed, ...skipped]);
  const idx = ONBOARDING_STEPS.indexOf(current as typeof ONBOARDING_STEPS[number]);
  for (let i = idx + 1; i < ONBOARDING_STEPS.length; i++) {
    if (!done.has(ONBOARDING_STEPS[i])) return ONBOARDING_STEPS[i];
  }
  return null;
}

/** Calculate progress percentage based on completed + skipped steps */
export function calcProgress(completed: string[], skipped: string[]): number {
  const done = new Set([...completed, ...skipped]);
  return Math.round((done.size / ONBOARDING_STEPS.length) * 100);
}

/** Parse raw D1 row into typed OnboardingFlow */
export function parseFlow(row: Record<string, unknown>): OnboardingFlow {
  return {
    id: row.id as string,
    tenant_id: row.tenant_id as string,
    current_step: row.current_step as string,
    completed_steps: JSON.parse((row.completed_steps as string) || '[]'),
    skipped_steps: JSON.parse((row.skipped_steps as string) || '[]'),
    metadata: JSON.parse((row.metadata as string) || '{}'),
    started_at: row.started_at as string,
    completed_at: (row.completed_at as string | null) ?? null,
    status: row.status as OnboardingFlow['status'],
  };
}

/** Insert an event record for audit/analytics */
export async function logEvent(
  db: D1Database,
  tenantId: string,
  step: string,
  action: string,
  metadata: Record<string, unknown> = {},
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO onboarding_events (id, tenant_id, step, action, metadata, created_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))`,
    )
    .bind(crypto.randomUUID(), tenantId, step, action, JSON.stringify(metadata))
    .run();
}
