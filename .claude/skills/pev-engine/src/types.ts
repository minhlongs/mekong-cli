/**
 * PEV Engine — Core TypeScript Interfaces
 *
 * Port of Mekong CLI's PEV (Plan-Execute-Verify) engine data models.
 * Pure TypeScript — no Python runtime dependency.
 */

// ─── Execution Modes ───────────────────────────────────────────────

export type StepMode = 'shell' | 'llm' | 'api' | 'tool' | 'browse';

// ─── Verification ──────────────────────────────────────────────────

export type VerificationStatus = 'passed' | 'failed' | 'warning' | 'skipped';

export interface VerificationCheck {
  name: string;
  status: VerificationStatus;
  message: string;
  expected?: string | number | boolean;
  actual?: string | number | boolean;
}

export interface VerificationCriteria {
  exit_code?: number;
  file_exists?: string[];
  file_not_exists?: string[];
  output_contains?: string[];
  output_not_contains?: string[];
}

export interface VerificationReport {
  passed: boolean;
  checks: VerificationCheck[];
  warnings: string[];
  errors: string[];
}

// ─── Execution Result ──────────────────────────────────────────────

export interface ExecutionResult {
  exit_code: number;
  stdout: string;
  stderr: string;
  output_files: string[];
  metadata: Record<string, unknown>;
  error?: Error;
}

// ─── Retry Policy ──────────────────────────────────────────────────

export type BackoffStrategy = 'fixed' | 'exponential' | 'full_jitter';

export interface RetryPolicy {
  max_attempts: number;
  initial_interval_ms: number;
  backoff: BackoffStrategy;
  max_interval_ms: number;
  non_retryable_exit_codes: number[];
}

export const DEFAULT_RETRY_POLICY: RetryPolicy = {
  max_attempts: 3,
  initial_interval_ms: 1000,
  backoff: 'exponential',
  max_interval_ms: 60000,
  non_retryable_exit_codes: [2],
};

// ─── Step Definition ───────────────────────────────────────────────

export interface Step {
  id: string;
  title: string;
  mode: StepMode;
  command: string;
  deps: string[];
  verify?: VerificationCriteria;
  retry?: Partial<RetryPolicy>;
  rollback?: string[];
  timeout_ms?: number;
  metadata?: Record<string, unknown>;
}

// ─── Step Result ───────────────────────────────────────────────────

export interface StepResult {
  step: Step;
  execution: ExecutionResult;
  verification: VerificationReport;
  attempts: number;
  self_healed: boolean;
  duration_ms: number;
}

// ─── Orchestration Status ──────────────────────────────────────────

export type OrchestrationStatus = 'success' | 'failed' | 'partial' | 'rolled_back';

export interface OrchestrationResult {
  status: OrchestrationStatus;
  steps: StepResult[];
  total_steps: number;
  completed_steps: number;
  failed_steps: number;
  warnings: string[];
  errors: string[];
  duration_ms: number;
  rollback_actions_run?: number;
}

// ─── DAG Types ─────────────────────────────────────────────────────

export interface DAGStepResult {
  order: number;
  success: boolean;
  result?: StepResult;
  error?: string;
}

// ─── Recipe ────────────────────────────────────────────────────────

export interface Recipe {
  name: string;
  description: string;
  steps: Step[];
  metadata: Record<string, unknown>;
}

// ─── Utility ───────────────────────────────────────────────────────

export function createStepResult(
  step: Step,
  execution: ExecutionResult,
  verification: VerificationReport,
  attempts: number = 1,
  self_healed: boolean = false,
): StepResult {
  return {
    step,
    execution,
    verification,
    attempts,
    self_healed,
    duration_ms: 0,
  };
}

export function createExecutionResult(
  overrides: Partial<ExecutionResult> = {},
): ExecutionResult {
  return {
    exit_code: 0,
    stdout: '',
    stderr: '',
    output_files: [],
    metadata: {},
    ...overrides,
  };
}

export function mergeRetryPolicy(
  base: RetryPolicy,
  override?: Partial<RetryPolicy>,
): RetryPolicy {
  if (!override) return base;
  return { ...base, ...override };
}
