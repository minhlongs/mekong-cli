import type { SopStep, StepState } from '../types/sop.js';
import { emit } from '../core/events.js';

export interface RollbackResult {
  success: boolean;
  rolledBack: string[];
  failed: string[];
  errors: string[];
}

/** Execute rollback for completed steps in reverse order */
export async function rollback(
  completedSteps: StepState[],
  stepDefinitions: SopStep[],
): Promise<RollbackResult> {
  const result: RollbackResult = {
    success: true,
    rolledBack: [],
    failed: [],
    errors: [],
  };

  // Reverse order — undo last completed step first
  const toRollback = [...completedSteps]
    .filter((s) => s.status === 'success')
    .reverse();

  for (const stepState of toRollback) {
    const stepDef = stepDefinitions.find((s) => s.id === stepState.stepId);
    if (!stepDef) continue;

    try {
      // Emit rollback event — callers can hook in custom undo logic
      emit('sop:step_completed', { stepId: stepState.stepId, action: 'rollback' });
      result.rolledBack.push(stepState.stepId);
    } catch (error) {
      result.success = false;
      result.failed.push(stepState.stepId);
      result.errors.push(`Rollback failed for ${stepState.stepId}: ${error}`);
    }
  }

  return result;
}
