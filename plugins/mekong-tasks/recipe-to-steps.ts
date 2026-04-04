/**
 * recipe-to-steps.ts — converts loaded Recipe objects into flat TaskStep arrays.
 *
 * Handles both JSON DAG recipes and Markdown step-list recipes.
 * Extracted from index.ts to keep files under 200 lines.
 */

import type {
  Recipe,
  JsonRecipe,
  MarkdownRecipe,
  TaskStep,
  DagGroup,
} from './types.js';

// ─── JSON DAG conversion ──────────────────────────────────────────────────────

/**
 * Converts a single DagGroup into TaskSteps, wiring inter-step dependencies.
 *
 * - parallel group: all commands share upstream deps (run concurrently)
 * - sequential group: each command depends on the previous one in the group
 */
function dagGroupToSteps(
  group: DagGroup,
  groupExitStepIds: Map<string, string[]>,
  maxRetries: number
): TaskStep[] {
  const upstreamDeps: string[] = group.depends_on.flatMap(
    (gid) => groupExitStepIds.get(gid) ?? []
  );

  const steps: TaskStep[] = [];
  let prevStepId: string | null = null;

  for (const cmd of group.commands) {
    const stepId = `${group.id}/${cmd.id}`;
    let deps: string[];

    if (group.mode === 'sequential') {
      deps = prevStepId !== null ? [prevStepId] : [...upstreamDeps];
    } else {
      deps = [...upstreamDeps];
    }

    steps.push({
      id: stepId,
      name: `${group.name} / ${cmd.id}`,
      command: `mekong ${cmd.id} ${cmd.args}`.trimEnd(),
      deps: [...new Set(deps)],
      maxRetries,
    });

    prevStepId = stepId;
  }

  return steps;
}

export function jsonRecipeToSteps(recipe: JsonRecipe, maxRetries: number): TaskStep[] {
  const allSteps: TaskStep[] = [];
  // group id → ids of that group's "exit" steps (used by downstream depends_on)
  const groupExitStepIds = new Map<string, string[]>();

  for (const group of recipe.dag.groups) {
    const steps = dagGroupToSteps(group, groupExitStepIds, maxRetries);
    allSteps.push(...steps);

    if (group.mode === 'parallel') {
      groupExitStepIds.set(group.id, steps.map((s) => s.id));
    } else {
      const last = steps[steps.length - 1];
      groupExitStepIds.set(group.id, last ? [last.id] : []);
    }
  }

  // Optional compile-summary step at the end
  const oc = recipe.dag.on_complete;
  if (oc?.compile_summary && oc.summary_file) {
    const allExits = [...groupExitStepIds.values()].flat();
    allSteps.push({
      id: 'on_complete/compile-summary',
      name: 'Compile Summary',
      command: `mekong compile-summary --output "${oc.summary_file}"`,
      deps: [...new Set(allExits)],
      maxRetries: 1,
    });
  }

  return allSteps;
}

// ─── Markdown conversion ──────────────────────────────────────────────────────

export function markdownRecipeToSteps(
  recipe: MarkdownRecipe,
  maxRetries: number
): TaskStep[] {
  return recipe.steps.map((step, i) => ({
    id: `step-${step.order}`,
    name: step.title,
    command: step.command,
    deps: i === 0 ? [] : [`step-${recipe.steps[i - 1].order}`],
    maxRetries,
  }));
}

// ─── Union dispatcher ─────────────────────────────────────────────────────────

export function recipeToTaskSteps(recipe: Recipe, maxRetries: number): TaskStep[] {
  if (recipe.format === 'json') return jsonRecipeToSteps(recipe, maxRetries);
  return markdownRecipeToSteps(recipe, maxRetries);
}

// ─── Placeholder substitution ─────────────────────────────────────────────────

/**
 * Replaces $ARGUMENTS and $KEY placeholders in step commands.
 */
export function applyArgs(
  steps: TaskStep[],
  args: Record<string, string>
): TaskStep[] {
  if (Object.keys(args).length === 0) return steps;

  const argStr = Object.entries(args)
    .map(([k, v]) => `${k}=${v}`)
    .join(' ');

  return steps.map((step) => ({
    ...step,
    command: Object.entries(args).reduce(
      (cmd, [k, v]) => cmd.replaceAll(`$${k}`, v),
      step.command.replaceAll('$ARGUMENTS', argStr)
    ),
  }));
}
