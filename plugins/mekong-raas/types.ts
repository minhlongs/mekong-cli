/**
 * types.ts — Shared TypeScript types for mekong-raas plugin.
 * All types used across tenant-auth, credit-meter, billing-logger, and index.
 */

/** Mekong layer names matching factory/layers.yaml */
export type MekongLayer =
  | 'studio'
  | 'founder'
  | 'business'
  | 'product'
  | 'engineering'
  | 'ops';

/** Credit cost per layer (from factory/layers.yaml layer ordering) */
export const LAYER_CREDIT_COSTS: Record<MekongLayer, number> = {
  studio: 10,
  founder: 8,
  business: 5,
  product: 3,
  engineering: 2,
  ops: 1,
};

/** Authenticated tenant parsed from Authorization header */
export interface Tenant {
  apiKey: string;
  tenantId: string;
  /** Credit balance available before this command */
  creditBalance: number;
  tier: string;
}

/** Result of credit validation and metering */
export interface CreditCheckResult {
  allowed: boolean;
  /** HTTP status code to return on denial */
  statusCode: 200 | 402 | 403 | 404;
  reason?: string;
  creditsRequired: number;
  remainingAfter: number;
}

/** Context object passed between before_dispatch and after_dispatch hooks */
export interface DispatchContext {
  /** Null = local use, no tenant, free */
  tenant: Tenant | null;
  command: string;
  layer: MekongLayer | null;
  creditsRequired: number;
  startedAt: number;
}

/** Billing ledger entry written in JSON Lines format */
export interface BillingLedgerEntry {
  ts: string; // ISO 8601
  tenantId: string;
  command: string;
  layer: MekongLayer | string;
  creditsUsed: number;
  durationMs: number;
  success: boolean;
  remainingCredits: number;
}

/** OpenClaw before_dispatch hook payload */
export interface BeforeDispatchPayload {
  command: string;
  args: string[];
  headers: Record<string, string | undefined>;
  layer?: string;
}

/** OpenClaw after_dispatch hook payload */
export interface AfterDispatchPayload {
  command: string;
  success: boolean;
  durationMs: number;
  context: DispatchContext;
}

/** Response returned by before_dispatch to allow or deny */
export interface HookResponse {
  /** If false, command is blocked */
  proceed: boolean;
  /** HTTP status code when blocking (402 = payment required) */
  statusCode?: number;
  reason?: string;
  /** Merged into dispatch context for after_dispatch */
  context?: DispatchContext;
}
