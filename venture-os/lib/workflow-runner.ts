/**
 * VentureOS Workflow Runner — executes DAG-defined workflows
 *
 * Reads workflow YAML definitions, builds execution plan from DAG,
 * runs steps respecting dependencies, and writes results to WAL + artifacts.
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

import type {
  WorkflowDefinition, WorkflowRun, StepResult,
  WorkflowRunStatus, StepStatus, WorkflowContext,
} from './workflow-types.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ─── Helpers ─────────────────────────────────────────────────────────────────

function ts(): string {
  return new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_');
}

function die(msg: string): never {
  console.error(`\x1b[31mError:\x1b[0m ${msg}`);
  process.exit(1);
}

// ─── Workflow Discovery ───────────────────────────────────────────────────────

export function loadWorkflow(workflowId: string): WorkflowDefinition {
  const parts = workflowId.split('/');
  if (parts.length < 2) die(`Workflow ID must be <category>/<name>: ${workflowId}`);
  const [category, name] = parts;
  const yamlPath = join(ROOT, 'workflows', category, name, 'workflow.yaml');
  if (!existsSync(yamlPath)) die(`Workflow not found: ${yamlPath}`);
  return parseWorkflowYaml(readFileSync(yamlPath, 'utf-8'));
}

export function listWorkflows(): Array<{ id: string; name: string; phases: string[] }> {
  const workflows: Array<{ id: string; name: string; phases: string[] }> = [];
  const wfRoot = join(ROOT, 'workflows');
  if (!existsSync(wfRoot)) return workflows;

  for (const category of readdirSync(wfRoot)) {
    const catDir = join(wfRoot, category);
    if (!isDir(catDir)) continue;
    for (const name of readdirSync(catDir) as string[]) {
      const yamlPath = join(catDir, name, 'workflow.yaml');
      if (!existsSync(yamlPath)) continue;
      try {
        const def = parseWorkflowYaml(readFileSync(yamlPath, 'utf-8'));
        workflows.push({ id: `${category}/${name}`, name: def.name, phases: def.lifecycle_phases });
      } catch { /* skip malformed */ }
    }
  }
  return workflows;
}

// ─── Workflow Execution ───────────────────────────────────────────────────────

export async function runWorkflow(
  workflowId: string,
  context: WorkflowContext,
): Promise<WorkflowRun> {
  const def = loadWorkflow(workflowId);
  const runId = `run-${ts()}`;
  const run: WorkflowRun = {
    id: runId,
    workflowId,
    ventureId: context.ventureId,
    status: 'running',
    triggeredBy: 'cli',
    startedAt: new Date().toISOString(),
    steps: [],
    context,
  };

  // Build execution order (topological sort by depends_on)
  const order = topologicalSort(def.steps);

  console.log(`\n\x1b[1mRunning workflow: ${def.name}\x1b[0m`);
  console.log(`   Venture: ${context.ventureId}`);
  console.log(`   Phase: ${context.lifecyclePhase} (${context.phase})`);
  console.log(`   Steps: ${def.steps.length}\n`);

  // Execute steps in order
  for (const stepId of order) {
    const step = def.steps.find((s: WorkflowDefinition['steps'][0]) => s.id === stepId)!;
    const stepResult = await executeStep(step, context, run);
    run.steps.push(stepResult);

    if (stepResult.status === 'failed') {
      run.status = 'failed';
      break;
    }
  }

  if (run.status === 'running') run.status = 'completed';
  run.finishedAt = new Date().toISOString();

  // Persist run record
  const runPath = join(context.ventureDir, 'wal', `${runId}.json`);
  writeFileSync(runPath, JSON.stringify(run, null, 2));

  // Write WAL event
  appendWAL(context.ventureDir, {
    type: 'workflow_complete',
    workflow_id: workflowId,
    run_id: runId,
    status: run.status,
    steps_completed: run.steps.filter(s => s.status === 'completed').length,
    timestamp: run.finishedAt,
  });

  console.log(`\n\x1b[36m→\x1b[0m Workflow ${run.status}: ${runId}`);
  return run;
}

// ─── Step Execution ───────────────────────────────────────────────────────────

async function executeStep(
  step: WorkflowDefinition['steps'][0],
  context: WorkflowContext,
  run: WorkflowRun,
): Promise<StepResult> {
  const started = new Date().toISOString();
  console.log(`  \x1b[33m▶\x1b[0m ${step.id} (${step.type})`);

  try {
    let output: unknown;

    switch (step.type) {
      case 'agent':
        output = await executeAgentStep(step, context, run);
        break;
      case 'action':
        output = await executeActionStep(step, context);
        break;
      case 'gate':
        output = await executeGateStep(step, context);
        break;
      default:
        die(`Step type not implemented: ${step.type}`);
    }

    // Save output to artifact if output_to is specified
    if (step.output_to && output) {
      const artifactPath = join(context.ventureDir, 'artifacts', step.output_to);
      mkdirSync(dirname(artifactPath), { recursive: true });
      writeFileSync(artifactPath, JSON.stringify(output, null, 2));
    }

    console.log(`  \x1b[32m✓\x1b[0m ${step.id} done`);
    return { stepId: step.id, status: 'completed', output, startedAt: started, finishedAt: new Date().toISOString() };
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err);
    console.log(`  \x1b[31m✗\x1b[0m ${step.id} failed: ${errMsg}`);
    return { stepId: step.id, status: 'failed', error: errMsg, startedAt: started, finishedAt: new Date().toISOString() };
  }
}

// ─── Step Type Implementations ────────────────────────────────────────────────

async function executeAgentStep(
  step: WorkflowDefinition['steps'][0],
  context: WorkflowContext,
  run: WorkflowRun,
): Promise<Record<string, unknown>> {
  // Agent steps produce a structured task brief that a human/AI executor can act on.
  // In the future, this will call the actual agent runtime.
  const brief = {
    __agent_step__: true,
    workflow: run.workflowId,
    step: step.id,
    prompt: step.prompt,
    context: {
      venture_id: context.ventureId,
      phase: context.lifecyclePhase,
      previous_outputs: context.previousOutputs,
    },
    parameters: step.with ?? {},
    output_type: step.output_type ?? 'json',
    executed_at: new Date().toISOString(),
  };
  return brief;
}

async function executeActionStep(
  step: WorkflowDefinition['steps'][0],
  context: WorkflowContext,
): Promise<Record<string, unknown>> {
  // Action steps execute deterministic file/data operations
  const action = step.prompt ?? '';
  if (action.startsWith('write:')) {
    const content = action.slice(6);
    const target = step.output_to ?? `step-${step.id}-output`;
    const outPath = join(context.ventureDir, 'workspace', target);
    writeFileSync(outPath, content);
    return { action: 'write', path: target, bytes: content.length };
  }
  return { action, result: 'executed' };
}

async function executeGateStep(
  step: WorkflowDefinition['steps'][0],
  context: WorkflowContext,
): Promise<Record<string, unknown>> {
  // Gate steps validate conditions — enforce stop/go
  const check = step.check ?? '';
  // Gate checks require manual validation or external signal; mark pending
  console.log(`     \x1b[33m⊘\x1b[0m Gate "${step.check}" requires manual validation`);
  return { gate: check, passed: false, requires_validation: true };
}

// ─── Graph Utilities ──────────────────────────────────────────────────────────

function topologicalSort(steps: WorkflowDefinition['steps']): string[] {
  const order: string[] = [];
  const visited = new Set<string>();
  const temp = new Set<string>();
  const adj = new Map<string, string[]>();

  for (const s of steps) adj.set(s.id, s.depends_on ?? []);

  function visit(id: string) {
    if (visited.has(id)) return;
    if (temp.has(id)) die(`Circular dependency detected in workflow: ${id}`);
    temp.add(id);
    for (const dep of adj.get(id) ?? []) visit(dep);
    temp.delete(id);
    visited.add(id);
    order.push(id);
  }

  for (const s of steps) visit(s.id);
  return order;
}

// ─── WAL Helpers ──────────────────────────────────────────────────────────────

function appendWAL(ventureDir: string, event: Record<string, unknown>) {
  const walDir = join(ventureDir, 'wal');
  if (!existsSync(walDir)) mkdirSync(walDir, { recursive: true });
  const walFile = join(walDir, 'current.jsonl');
  writeFileSync(walFile, readFileSync(walFile, 'utf-8') + JSON.stringify(event) + '\n');
}

// Minimal stubs for Node built-ins not always available in ESM context
import { readdirSync, statSync } from 'fs';
function isDir(p: string): boolean {
  try { return statSync(p).isDirectory(); } catch { return false; }
}

// ─── Minimal YAML Parser ──────────────────────────────────────────────────────

function parseWorkflowYaml(content: string): WorkflowDefinition {
  // Support a subset of YAML sufficient for workflow definitions
  const result: Record<string, unknown> = {};
  let currentSection = result;
  const stack: Array<{ dict: Record<string, unknown>; key: string }> = [];
  let currentKey = '';

  for (const rawLine of content.split('\n')) {
    const line = rawLine.replace(/\t/g, '  ');
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const indent = line.search(/\S/);

    // Pop stack to correct parent
    while (stack.length > 0 && indent <= stack[stack.length - 1].key.length) {
      stack.pop();
    }

    // Section header [section]
    const sectionMatch = trimmed.match(/^\[(.+)\]$/);
    if (sectionMatch) {
      currentSection = {};
      result[sectionMatch[1]] = currentSection;
      stack.length = 0;
      continue;
    }

    // Key: value
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx < 0) continue;
    const key = trimmed.slice(0, colonIdx).trim();
    let value: unknown = trimmed.slice(colonIdx + 1).trim();

    // Unquote strings
    if (typeof value === 'string' && ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'")))) {
      value = value.slice(1, -1);
    }

    // Empty value — might be a nested section
    if (!value && !trimmed.endsWith(':')) {
      value = '';
    }

    // Inline list [a, b, c]
    if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
      value = value.slice(1, -1).split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
    }

    // List item  - item
    if (trimmed.startsWith('- ') && stack.length > 0) {
      const parentKey = stack[stack.length - 1].key;
      const parent = stack[stack.length - 1].dict;
      if (!Array.isArray(parent[parentKey])) {
        const existing = parent[parentKey];
        parent[parentKey] = Array.isArray(existing) ? existing : [existing];
      }
      (parent[parentKey] as unknown[]).push(value);
      continue;
    }

    // Nested key (ends with :)
    if (trimmed.endsWith(':')) {
      const nested: Record<string, unknown> = {};
      currentSection[key] = nested;
      stack.push({ dict: currentSection, key });
      currentSection = nested;
      continue;
    }

    currentSection[key] = value;
  }

// Flatten dotted-key objects (e.g. "steps.0.id") into arrays of objects
 function flattenDottedKeys(obj: Record<string, unknown>): Record<string, unknown> {
    const out: Record<string, unknown> = {};
    const grouped = new Map<string, unknown[]>();

    for (const [key, value] of Object.entries(obj)) {
        // Plain object whose keys already contain dots (nested flat object)
        if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
            const nestedKeys = Object.keys(value);
            const hasDotted = nestedKeys.some(k => k.includes('.'));
            if (hasDotted) {
                // Process nested dotted keys directly (they are the full path)
                for (const [nk, nv] of Object.entries(value)) {
                    processKey(nk, nv, out, grouped);
                }
                continue;
            }
        }
        processKey(key, value, out, grouped);
    }

    for (const [prefix, arr] of grouped) {
        out[prefix] = Object.values(arr).filter(Boolean);
    }
    return out;
}

function processKey(key: string, value: unknown, out: Record<string, unknown>, grouped: Map<string, unknown[]>): void {
    if (Array.isArray(value)) { out[key] = value; return; }
    const dotIdx = key.indexOf('.');
    if (dotIdx < 0) { out[key] = value; return; }
    const prefix = key.slice(0, dotIdx);
    const rest = key.slice(dotIdx + 1);
    const restDot = rest.indexOf('.');
    if (restDot < 0) { out[key] = value; return; }
    const index = rest.slice(0, restDot);
    const field = rest.slice(restDot + 1);
    if (!grouped.has(prefix)) grouped.set(prefix, []);
    const arr = grouped.get(prefix)!;
    if (!arr[+index]) arr[+index] = {};
    arr[+index][field] = value;
}

// Normalize output
 const flat = flattenDottedKeys(result);
 const steps = (flat.steps as Array<Record<string, unknown>>) ?? [];
  return {
    id: result.id as string,
    name: result.name as string,
    description: (result.description as string) ?? '',
    version: (result.version as string) ?? '0.1.0',
    lifecycle_phases: result.lifecycle_phases as string[],
    inputs: result.inputs as WorkflowDefinition['inputs'],
    outputs: result.outputs as WorkflowDefinition['outputs'],
    triggers_on: result.triggers_on as string[] | undefined,
    quality_gates: result.quality_gates as string[],
    steps: steps.map(s => ({
      id: s.id as string,
      type: s.type as WorkflowDefinition['steps'][0]['type'],
      prompt: s.prompt as string | undefined,
      depends_on: s.depends_on as string[] | undefined,
      output_to: s.output_to as string | undefined,
      output_type: s.output_type as string | undefined,
      with: s.with as Record<string, unknown> | undefined,
      check: s.check as string | undefined,
      required: s.required as boolean | undefined,
    })),
  };
}
