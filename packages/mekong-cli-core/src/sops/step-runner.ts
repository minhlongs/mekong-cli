import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import type { SopDefinition, SopRun, SopStep } from '../types/sop.js';
import type { ToolRegistry } from '../tools/registry.js';
import type { LlmRouter } from '../llm/router.js';
import type { OrchestratorAgent } from '../agents/orchestrator.js';
import { generateId } from '../utils/hash.js';

const execAsync = promisify(exec);

/** Resolver function that loads a SOP definition by name */
export type SopResolver = (sopName: string) => Promise<SopDefinition | undefined>;

export interface ExecutorDeps {
  tools?: ToolRegistry;
  llm?: LlmRouter;
  orchestrator?: OrchestratorAgent;
  sopResolver?: SopResolver;
  askUser?: (question: string) => Promise<string>;
}

const MAX_SOP_DEPTH = 10;

/** Interpolate {variables} in template strings */
export function interpolateTemplate(template: string, context: Record<string, unknown>): string {
  return template.replace(/\{([^}]+)\}/g, (_, key: string) => {
    const value = context[key];
    return value !== undefined ? String(value) : `{${key}}`;
  });
}

/** Simple condition evaluation */
export function evaluateStepCondition(condition: string, context: Record<string, unknown>): boolean {
  if (condition === 'true') return true;
  if (condition === 'false') return false;
  return Boolean(context[condition]);
}

/** Check a precondition */
export async function checkSopPrecondition(pre: { type: string; value: string }): Promise<boolean> {
  switch (pre.type) {
    case 'env_set':
      return process.env[pre.value] !== undefined;
    case 'command_available':
      try {
        await execAsync(`which ${pre.value}`);
        return true;
      } catch {
        return false;
      }
    case 'file_exists':
      try {
        const { stat } = await import('node:fs/promises');
        await stat(pre.value);
        return true;
      } catch {
        return false;
      }
    case 'custom':
      try {
        await execAsync(pre.value);
        return true;
      } catch {
        return false;
      }
    default:
      return true;
  }
}

/** Run the actual action of a SOP step */
export async function runStepAction(
  step: SopStep,
  context: Record<string, unknown>,
  deps: ExecutorDeps,
  depth: number,
  runNestedSop: (sop: SopDefinition, inputs: Record<string, unknown>, nextDepth: number) => Promise<SopRun>,
): Promise<unknown> {
  switch (step.action) {
    case 'shell': {
      if (!step.command) throw new Error('Shell step missing command');
      const cmd = interpolateTemplate(step.command, context);
      const timeout = (step.timeout_seconds ?? 300) * 1000;
      const { stdout } = await execAsync(cmd, { timeout });
      return stdout.trim();
    }
    case 'tool': {
      if (!step.tool) throw new Error('Tool step missing tool name');
      if (!deps.tools) throw new Error('ToolRegistry not provided');
      const result = await deps.tools.execute(step.tool, step.inputs ?? {});
      if (!result.success) throw new Error(result.error ?? 'Tool failed');
      return result.output;
    }
    case 'condition':
      return evaluateStepCondition(step.condition ?? 'true', context);
    case 'llm': {
      if (!deps.llm) throw new Error('LlmRouter not provided');
      if (!step.prompt) throw new Error('LLM step missing prompt');
      const prompt = interpolateTemplate(step.prompt, context);
      const response = await deps.llm.chat({
        messages: [{ role: 'user', content: prompt }],
        maxTokens: 2048,
      });
      return response.content;
    }
    case 'agent': {
      if (!deps.orchestrator) throw new Error('OrchestratorAgent not provided');
      if (!step.prompt) throw new Error('Agent step missing prompt');
      const taskPrompt = interpolateTemplate(step.prompt, context);
      const agentType = step.tool ?? 'default';
      const task = {
        id: generateId('task'),
        description: taskPrompt,
        agentId: agentType,
        priority: 'normal' as const,
        inputs: step.inputs ?? {},
        expectedOutputs: [],
        timeout: (step.timeout_seconds ?? 300) * 1000,
        retryCount: 0,
        maxRetries: step.retry?.max ?? 0,
      };
      const plan = deps.orchestrator.plan([task]);
      const orchResult = await deps.orchestrator.execute(plan, agentType);
      if (!orchResult.success) {
        throw new Error(`Agent task failed: ${orchResult.failedCount} failures`);
      }
      return orchResult.results.map(r => r.payload.content).join('\n');
    }
    case 'sop': {
      if (!step.sop) throw new Error('SOP step missing sop name');
      if (!deps.sopResolver) throw new Error('SopResolver not provided');
      if (depth >= MAX_SOP_DEPTH) {
        throw new Error(`SOP recursion depth exceeded (max ${MAX_SOP_DEPTH})`);
      }
      const nestedSop = await deps.sopResolver(step.sop);
      if (!nestedSop) throw new Error(`SOP "${step.sop}" not found`);
      const nestedRun = await runNestedSop(nestedSop, step.inputs ?? {}, depth + 1);
      if (nestedRun.status === 'failed') {
        throw new Error(`Nested SOP "${step.sop}" failed: ${nestedRun.error}`);
      }
      return nestedRun.outputs;
    }
    default:
      throw new Error(`Unknown action: ${step.action}`);
  }
}
