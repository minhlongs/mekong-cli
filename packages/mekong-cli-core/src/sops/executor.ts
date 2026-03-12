import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import type { SopDefinition, SopRun, SopStep, StepState } from '../types/sop.js';
import type { ToolRegistry } from '../tools/registry.js';
import type { LlmRouter } from '../llm/router.js';
import type { OrchestratorAgent } from '../agents/orchestrator.js';
import { buildDag, topoSort } from './dag.js';
import { generateId } from '../utils/hash.js';
import { emit } from '../core/events.js';

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

export class SopExecutor {
  private deps: ExecutorDeps;
  private depth: number;

  constructor(deps: ExecutorDeps = {}, depth: number = 0) {
    this.deps = deps;
    this.depth = depth;
  }

  /** Run a SOP definition with resolved inputs */
  async run(sop: SopDefinition, userInputs: Record<string, unknown> = {}): Promise<SopRun> {
    const run: SopRun = {
      id: generateId('run'),
      sopName: sop.sop.name,
      sopVersion: sop.sop.version,
      status: 'running',
      startedAt: new Date().toISOString(),
      inputs: userInputs,
      outputs: {},
      steps: [],
    };

    emit('sop:started', { runId: run.id, sopName: run.sopName });

    // Check preconditions
    for (const pre of sop.sop.preconditions) {
      const passed = await this.checkPrecondition(pre);
      if (!passed) {
        run.status = 'failed';
        run.error = `Precondition failed: ${pre.message ?? pre.value}`;
        run.completedAt = new Date().toISOString();
        emit('sop:failed', { runId: run.id, error: run.error });
        return run;
      }
    }

    // Build DAG and get execution layers
    const dagNodes = buildDag(sop.sop.steps);
    let layers;
    try {
      layers = topoSort(dagNodes);
    } catch (error) {
      run.status = 'failed';
      run.error = error instanceof Error ? error.message : String(error);
      run.completedAt = new Date().toISOString();
      emit('sop:failed', { runId: run.id, error: run.error });
      return run;
    }

    // Build interpolation context
    const context: Record<string, unknown> = { ...userInputs };

    // Execute layer by layer
    for (const layer of layers) {
      const layerPromises = layer.stepIds.map(async (stepId) => {
        const step = sop.sop.steps.find((s) => s.id === stepId)!;
        return this.executeStep(step, context);
      });

      const layerResults = await Promise.all(layerPromises);

      for (const stepState of layerResults) {
        run.steps.push(stepState);
        if (stepState.output !== undefined) {
          context[`step.${stepState.stepId}.output`] = stepState.output;
        }

        emit('sop:step_completed', {
          runId: run.id,
          stepId: stepState.stepId,
          status: stepState.status,
        });

        if (stepState.status === 'failed') {
          const stepDef = sop.sop.steps.find((s) => s.id === stepState.stepId);
          if (!stepDef || stepDef.on_failure === 'stop') {
            run.status = 'failed';
            run.error = `Step "${stepState.stepId}" failed: ${stepState.error}`;
            run.completedAt = new Date().toISOString();
            emit('sop:failed', { runId: run.id, error: run.error });
            return run;
          }
          // 'continue' — keep going; 'retry' handled in executeStep
        }
      }
    }

    run.status = 'success';
    run.outputs = Object.fromEntries(
      run.steps
        .filter((s) => s.output !== undefined)
        .map((s) => [s.stepId, s.output]),
    );
    run.completedAt = new Date().toISOString();
    emit('sop:completed', { runId: run.id });
    return run;
  }

  /** Execute a single step with retry logic */
  private async executeStep(
    step: SopStep,
    context: Record<string, unknown>,
  ): Promise<StepState> {
    const state: StepState = {
      stepId: step.id,
      status: 'running',
      startedAt: new Date().toISOString(),
      retryCount: 0,
    };

    // Check condition
    if (step.condition) {
      const conditionMet = this.evaluateCondition(step.condition, context);
      if (!conditionMet) {
        state.status = 'skipped';
        state.output = 'skipped: condition not met';
        state.completedAt = new Date().toISOString();
        return state;
      }
    }

    const maxRetries = step.retry?.max ?? 0;
    const retryDelay = (step.retry?.delay_seconds ?? 5) * 1000;

    while (state.retryCount <= maxRetries) {
      try {
        const output = await this.runAction(step, context);
        state.status = 'success';
        state.output = output;
        state.completedAt = new Date().toISOString();
        return state;
      } catch (error) {
        state.retryCount++;
        state.error = error instanceof Error ? error.message : String(error);

        if (state.retryCount <= maxRetries && step.on_failure === 'retry') {
          await new Promise((resolve) => setTimeout(resolve, retryDelay));
        } else {
          break;
        }
      }
    }

    state.status = 'failed';
    state.completedAt = new Date().toISOString();
    return state;
  }

  /** Run the actual action */
  private async runAction(step: SopStep, context: Record<string, unknown>): Promise<unknown> {
    switch (step.action) {
      case 'shell': {
        if (!step.command) throw new Error('Shell step missing command');
        const cmd = this.interpolate(step.command, context);
        const timeout = (step.timeout_seconds ?? 300) * 1000;
        const { stdout } = await execAsync(cmd, { timeout });
        return stdout.trim();
      }
      case 'tool': {
        if (!step.tool) throw new Error('Tool step missing tool name');
        if (!this.deps.tools) throw new Error('ToolRegistry not provided');
        const result = await this.deps.tools.execute(step.tool, step.inputs ?? {});
        if (!result.success) throw new Error(result.error ?? 'Tool failed');
        return result.output;
      }
      case 'condition':
        return this.evaluateCondition(step.condition ?? 'true', context);
      case 'llm': {
        if (!this.deps.llm) throw new Error('LlmRouter not provided');
        if (!step.prompt) throw new Error('LLM step missing prompt');
        const prompt = this.interpolate(step.prompt, context);
        const response = await this.deps.llm.chat({
          messages: [{ role: 'user', content: prompt }],
          maxTokens: 2048,
        });
        return response.content;
      }
      case 'agent': {
        if (!this.deps.orchestrator) throw new Error('OrchestratorAgent not provided');
        if (!step.prompt) throw new Error('Agent step missing prompt');
        const taskPrompt = this.interpolate(step.prompt, context);
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
        const plan = this.deps.orchestrator.plan([task]);
        const orchResult = await this.deps.orchestrator.execute(plan, agentType);
        if (!orchResult.success) {
          throw new Error(`Agent task failed: ${orchResult.failedCount} failures`);
        }
        return orchResult.results.map(r => r.payload.content).join('\n');
      }
      case 'sop': {
        if (!step.sop) throw new Error('SOP step missing sop name');
        if (!this.deps.sopResolver) throw new Error('SopResolver not provided');
        if (this.depth >= MAX_SOP_DEPTH) {
          throw new Error(`SOP recursion depth exceeded (max ${MAX_SOP_DEPTH})`);
        }
        const nestedSop = await this.deps.sopResolver(step.sop);
        if (!nestedSop) throw new Error(`SOP "${step.sop}" not found`);
        const childExecutor = new SopExecutor(this.deps, this.depth + 1);
        const nestedRun = await childExecutor.run(nestedSop, step.inputs ?? {});
        if (nestedRun.status === 'failed') {
          throw new Error(`Nested SOP "${step.sop}" failed: ${nestedRun.error}`);
        }
        return nestedRun.outputs;
      }
      default:
        throw new Error(`Unknown action: ${step.action}`);
    }
  }

  /** Interpolate {variables} in template strings */
  private interpolate(template: string, context: Record<string, unknown>): string {
    return template.replace(/\{([^}]+)\}/g, (_, key: string) => {
      const value = context[key];
      return value !== undefined ? String(value) : `{${key}}`;
    });
  }

  /** Simple condition evaluation */
  private evaluateCondition(condition: string, context: Record<string, unknown>): boolean {
    if (condition === 'true') return true;
    if (condition === 'false') return false;
    return Boolean(context[condition]);
  }

  /** Check a precondition */
  private async checkPrecondition(pre: { type: string; value: string }): Promise<boolean> {
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
}
