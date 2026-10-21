import type { SopDefinition, SopRun, SopStep, StepState } from '../types/sop.js';
import { buildDag, topoSort } from './dag.js';
import { generateId } from '../utils/hash.js';
import { emit } from '../core/events.js';
import {
  checkSopPrecondition,
  evaluateStepCondition,
  runStepAction,
  type ExecutorDeps,
  type SopResolver,
} from './step-runner.js';

export type { ExecutorDeps, SopResolver };

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

    for (const pre of sop.sop.preconditions) {
      const passed = await checkSopPrecondition(pre);
      if (!passed) {
        run.status = 'failed';
        run.error = `Precondition failed: ${pre.message ?? pre.value}`;
        run.completedAt = new Date().toISOString();
        emit('sop:failed', { runId: run.id, error: run.error });
        return run;
      }
    }

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

    const context: Record<string, unknown> = { ...userInputs };

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

    if (step.condition) {
      const conditionMet = evaluateStepCondition(step.condition, context);
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
        const output = await runStepAction(
          step,
          context,
          this.deps,
          this.depth,
          (nestedSop, inputs, nextDepth) => new SopExecutor(this.deps, nextDepth).run(nestedSop, inputs),
        );
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
}
