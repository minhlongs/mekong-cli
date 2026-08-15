/**
 * VentureOS Workflow Engine — core types
 *
 * Workflows are YAML-defined DAGs executed by the CLI.
 * Each workflow targets one or more lifecycle phases.
 */

export interface WorkflowContext {
  ventureId: string;
  ventureDir: string;
  phase: string;
  lifecyclePhase: string;
  previousOutputs: Record<string, unknown>;
}

export interface WorkflowStep {
  id: string;
  type: 'agent' | 'parallel' | 'workflow_call' | 'action' | 'gate';
  prompt?: string;
  depends_on?: string[];
  output_to?: string;
  output_type?: string;
  with?: Record<string, unknown>;
  // for gate type
  check?: string;
  required?: boolean;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description: string;
  version: string;
  lifecycle_phases: string[];
  inputs: Record<string, { type: string; required: boolean; path?: string }>;
  outputs: Record<string, { type: string; path: string }>;
  triggers_on?: string[];
  steps: WorkflowStep[];
  quality_gates: string[];
}

export type WorkflowRunStatus = 'pending' | 'running' | 'completed' | 'failed';
export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface StepResult {
  stepId: string;
  status: StepStatus;
  output?: unknown;
  error?: string;
  startedAt: string;
  finishedAt: string;
}

export interface WorkflowRun {
  id: string;
  workflowId: string;
  ventureId: string;
  status: WorkflowRunStatus;
  triggeredBy: string;
  startedAt: string;
  finishedAt?: string;
  steps: StepResult[];
  context: WorkflowContext;
}

export const PHASES: Record<string, string> = {
  '01': 'IDENTIFY',
  '02': 'IDEA',
  '03': 'VALIDATE',
  '04': 'ARCHITECT',
  '05': 'INCORPORATE',
  '06': 'SEED',
  '07': 'BUILD',
  '08': 'SCALE',
  '09': 'EXIT',
};

// ─── WAL Event Types ──────────────────────────────────────────────────────────

export interface WALEvent {
  type: string;
  timestamp: string;
}

export interface WorkflowChainStepEvent extends WALEvent {
  type: 'workflow_chain_step' | 'workflow_chain_complete';
  workflow_id: string;
  status: string;
  step?: number;
  total_steps?: number;
  artifacts?: string[];
  error?: string;
  total?: number;
  succeeded?: number;
  failed?: number;
  run_id?: string;
}

export const LIFE_TO_CLAUDE_PROMPT: Record<string, string> = {
  IDENTIFY: 'Research market problems, identify unmet needs, define opportunity space',
  IDEA: 'Brainstorm solutions, evaluate feasibility, select top 2-3 candidates',
  VALIDATE: 'Build landing page, run Sean Ellis test, measure demand signal',
  ARCHITECT: 'Design system architecture, choose tech stack, plan MVP',
  INCORPORATE: 'Entity setup, cap table, legal docs, banking',
  SEED: 'Build MVP, onboard first users, iterate rapidly',
  BUILD: 'Scale engineering, hire key roles, establish operations',
  SCALE: 'Expand markets, optimize unit economics, build moats',
  EXIT: 'Prepare for acquisition/IPO, maximize valuation',
};
