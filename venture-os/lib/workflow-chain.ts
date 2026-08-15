/**
 * VentureOS Workflow Chain — sequential multi-workflow execution
 *
 * Runs a sequence of workflows on a single venture, tracking chain state
 * and emitting WAL events for each step.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

import { loadWorkflow, runWorkflow } from './workflow-runner.js';
import type { WorkflowContext } from './workflow-types.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ─── Helpers ──────────────────────────────────────────────────────────────────

function ts(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
}

function today(): string {
  return new Date().toISOString().split('T')[0].replace(/-/g, '');
}

function appendWAL(ventureDir: string, event: Record<string, unknown>) {
  const walDir = join(ventureDir, 'wal');
  if (!existsSync(walDir)) mkdirSync(walDir, { recursive: true });
  const walFile = join(walDir, 'current.jsonl');
  writeFileSync(walFile, readFileSync(walFile, 'utf-8') + JSON.stringify(event) + '\n');
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ChainStepResult {
  workflow_id: string;
  status: 'completed' | 'failed';
  artifacts: string[];
  error?: string;
  run_id: string;
}

export interface ChainResult {
  total: number;
  succeeded: number;
  failed: number;
  artifacts: string[];
  steps: ChainStepResult[];
}

export interface ChainState {
  venture_id: string;
  started_at: string;
  updated_at: string;
  status: 'running' | 'completed' | 'failed';
  completed_workflows: string[];
  failed_workflow?: string;
  step_results: ChainStepResult[];
}

// ─── State Management ─────────────────────────────────────────────────────────

function chainStatePath(ventureDir: string): string {
  return join(ventureDir, 'state', 'chain-state.json');
}

function loadChainState(ventureDir: string): ChainState | null {
  const p = chainStatePath(ventureDir);
  if (!existsSync(p)) return null;
  return JSON.parse(readFileSync(p, 'utf-8'));
}

function saveChainState(ventureDir: string, state: ChainState) {
  const p = chainStatePath(ventureDir);
  mkdirSync(dirname(p), { recursive: true });
  state.updated_at = today();
  writeFileSync(p, JSON.stringify(state, null, 2));
}

// ─── Chain Execution ──────────────────────────────────────────────────────────

export async function chainWorkflows(
  ventureId: string,
  workflowIds: string[],
): Promise<ChainResult> {
  // Find venture directory
  const ventureDir = join(ROOT, 'ventures', ventureId);
  if (!existsSync(ventureDir)) {
    console.error(`\x1b[31mError:\x1b[0m Venture not found: ${ventureId}`);
    process.exit(1);
  }

  if (workflowIds.length === 0) {
    console.error('Usage: chainWorkflows(ventureId, [wf1, wf2, ...]) — workflowIds cannot be empty');
    process.exit(1);
  }

  // Load venture state for context
  const stateJson = JSON.parse(readFileSync(join(ventureDir, 'state.json'), 'utf-8'));

  const steps: ChainStepResult[] = [];
  const allArtifacts: string[] = [];
  let succeeded = 0;
  let failed = 0;

  // Initialize chain state
  const chainState: ChainState = {
    venture_id: ventureId,
    started_at: ts(),
    updated_at: today(),
    status: 'running',
    completed_workflows: [],
    step_results: [],
  };
  saveChainState(ventureDir, chainState);

  console.log(`\n\x1b[1mWorkflow Chain: ${ventureId}\x1b[0m`);
  console.log(` Steps: ${workflowIds.length}`);
  console.log(` Started: ${chainState.started_at}\n`);

  for (let i = 0; i < workflowIds.length; i++) {
    const wfId = workflowIds[i];
    const stepNum = i + 1;
    const totalSteps = workflowIds.length;

    // WAL event: step start
    appendWAL(ventureDir, {
      type: 'workflow_chain_step',
      workflow_id: wfId,
      status: 'started',
      step: stepNum,
      total_steps: totalSteps,
      timestamp: ts(),
    });

    // Load workflow definition to display name
    const def = loadWorkflow(wfId);

    console.log(`\n\x1b[36m── Chain Step ${stepNum}/${totalSteps}: ${def.name} (${wfId}) ──\x1b[0m`);

    // Build context
    const ctx: WorkflowContext = {
      ventureId,
      ventureDir,
      phase: stateJson.current_phase ?? '01',
      lifecyclePhase: stateJson.phase_label ?? 'IDENTIFY',
      previousOutputs: {},
    };

    let stepResult: ChainStepResult;
    try {
      const run = await runWorkflow(wfId, ctx);

      // Collect artifacts from the workflow run
      const artifacts: string[] = [];
      for (const step of run.steps) {
        if (step.status === 'completed' && step.output_to) {
          const artifactPath = join(ventureDir, 'artifacts', step.output_to);
          artifacts.push(artifactPath);
          allArtifacts.push(artifactPath);
        }
      }

      stepResult = {
        workflow_id: wfId,
        status: run.status === 'completed' ? 'completed' : 'failed',
        artifacts,
        run_id: run.id,
      };

      if (run.status === 'failed') {
        stepResult.error = run.steps.find(s => s.status === 'failed')?.error ?? 'unknown error';
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      console.log(` \x1b[31m✗\x1b[0m Chain step failed: ${wfId}: ${errMsg}`);
      stepResult = {
        workflow_id: wfId,
        status: 'failed',
        artifacts: [],
        error: errMsg,
        run_id: '',
      };
    }

    steps.push(stepResult);

    if (stepResult.status === 'completed') {
      succeeded++;
      chainState.completed_workflows.push(wfId);
      appendWAL(ventureDir, {
        type: 'workflow_chain_step',
        workflow_id: wfId,
        status: 'completed',
        step: stepNum,
        total_steps: totalSteps,
        artifacts: stepResult.artifacts,
        run_id: stepResult.run_id,
        timestamp: ts(),
      });
    } else {
      failed++;
      chainState.status = 'failed';
      chainState.failed_workflow = wfId;
      appendWAL(ventureDir, {
        type: 'workflow_chain_step',
        workflow_id: wfId,
        status: 'failed',
        step: stepNum,
        total_steps: totalSteps,
        error: stepResult.error,
        timestamp: ts(),
      });

      // Stop chain on failure
      saveChainState(ventureDir, chainState);
      console.log(`\n\x1b[31m✗ Chain stopped at step ${stepNum}/${totalSteps} due to failure.\x1b[0m`);
      return {
        total: workflowIds.length,
        succeeded,
        failed,
        artifacts: allArtifacts,
        steps,
      };
    }
  }

  // Mark chain complete
  chainState.status = 'completed';
  saveChainState(ventureDir, chainState);

  // Final WAL event
  appendWAL(ventureDir, {
    type: 'workflow_chain_complete',
    total: workflowIds.length,
    succeeded,
    failed,
    artifacts: allArtifacts,
    timestamp: ts(),
  });

  return {
    total: workflowIds.length,
    succeeded,
    failed,
    artifacts: allArtifacts,
    steps,
  };
}
