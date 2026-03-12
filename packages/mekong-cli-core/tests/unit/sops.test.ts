import { describe, it, expect, beforeEach } from 'vitest';
import { parseSopYaml, parseSopFile } from '../../src/sops/parser.js';
import { buildDag, topoSort, validateDag } from '../../src/sops/dag.js';
import { SopExecutor } from '../../src/sops/executor.js';
import { rollback } from '../../src/sops/rollback.js';
import { collectMetrics, compareRuns } from '../../src/sops/metrics.js';
import type { SopDefinition, SopStep, StepState, SopRun } from '../../src/types/sop.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MINIMAL_SOP_YAML = `
sop:
  name: test-sop
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions: []
  steps:
    - id: step1
      name: "Step 1"
      action: shell
      command: "echo hello"
      on_failure: stop
`;

const TWO_STEP_SOP_YAML = `
sop:
  name: two-step
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions: []
  steps:
    - id: step1
      name: "Step 1"
      action: shell
      command: "echo first"
      on_failure: stop
      on_success: step2
    - id: step2
      name: "Step 2"
      action: shell
      command: "echo second"
      on_failure: stop
`;

function makeStep(id: string, on_success?: string): SopStep {
  return {
    id,
    name: id,
    action: 'shell',
    command: `echo ${id}`,
    on_failure: 'stop',
    on_success,
  };
}

function makeStepState(stepId: string, status: StepState['status'] = 'success'): StepState {
  return {
    stepId,
    status,
    startedAt: new Date(Date.now() - 100).toISOString(),
    completedAt: new Date().toISOString(),
    retryCount: 0,
  };
}

function makeRun(overrides: Partial<SopRun> = {}): SopRun {
  return {
    id: 'run_test',
    sopName: 'test',
    sopVersion: '1.0.0',
    status: 'success',
    startedAt: new Date(Date.now() - 1000).toISOString(),
    completedAt: new Date().toISOString(),
    inputs: {},
    outputs: {},
    steps: [],
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Parser tests
// ---------------------------------------------------------------------------

describe('parseSopYaml', () => {
  it('parses valid YAML successfully', () => {
    const result = parseSopYaml(MINIMAL_SOP_YAML);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.sop.name).toBe('test-sop');
      expect(result.value.sop.steps).toHaveLength(1);
    }
  });

  it('returns error for YAML missing steps field', () => {
    const yaml = `
sop:
  name: bad-sop
  version: "1.0.0"
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(false);
  });

  it('returns error for completely invalid YAML structure', () => {
    const result = parseSopYaml('not_a_sop: true');
    expect(result.ok).toBe(false);
  });

  it('parses SOP with multiple steps and on_success chain', () => {
    const result = parseSopYaml(TWO_STEP_SOP_YAML);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.sop.steps).toHaveLength(2);
      expect(result.value.sop.steps[0].on_success).toBe('step2');
    }
  });
});

describe('parseSopFile', () => {
  it('returns error for non-existent file', async () => {
    const result = await parseSopFile('/tmp/non-existent-sop-file-xyz.yaml');
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.error.message).toContain('Failed to read SOP file');
    }
  });
});

// ---------------------------------------------------------------------------
// DAG tests
// ---------------------------------------------------------------------------

describe('buildDag', () => {
  it('builds linear chain: A→B→C via on_success', () => {
    const steps = [
      makeStep('a', 'b'),
      makeStep('b', 'c'),
      makeStep('c'),
    ];
    const dag = buildDag(steps);
    const aNode = dag.find((n) => n.step.id === 'a')!;
    const bNode = dag.find((n) => n.step.id === 'b')!;
    const cNode = dag.find((n) => n.step.id === 'c')!;

    expect(aNode.dependencies).toEqual([]);
    expect(bNode.dependencies).toEqual(['a']);
    expect(cNode.dependencies).toEqual(['b']);
  });

  it('builds dag with no dependencies when no on_success set', () => {
    const steps = [makeStep('x'), makeStep('y'), makeStep('z')];
    const dag = buildDag(steps);
    for (const node of dag) {
      expect(node.dependencies).toEqual([]);
    }
  });
});

describe('topoSort', () => {
  it('produces correct layers for linear chain', () => {
    const steps = [makeStep('a', 'b'), makeStep('b', 'c'), makeStep('c')];
    const dag = buildDag(steps);
    const layers = topoSort(dag);

    expect(layers).toHaveLength(3);
    expect(layers[0].stepIds).toEqual(['a']);
    expect(layers[1].stepIds).toEqual(['b']);
    expect(layers[2].stepIds).toEqual(['c']);
  });

  it('places independent steps in same layer', () => {
    const steps = [makeStep('x'), makeStep('y'), makeStep('z')];
    const dag = buildDag(steps);
    const layers = topoSort(dag);

    expect(layers).toHaveLength(1);
    expect(layers[0].stepIds).toHaveLength(3);
  });

  it('throws on circular dependency', () => {
    // Manually craft circular nodes (can't do it via on_success since both would need to point to each other)
    const nodes = [
      { step: makeStep('a'), dependencies: ['b'] },
      { step: makeStep('b'), dependencies: ['a'] },
    ];
    expect(() => topoSort(nodes)).toThrow('Circular dependency detected');
  });
});

describe('validateDag', () => {
  it('returns valid for correct dag', () => {
    const steps = [makeStep('a', 'b'), makeStep('b')];
    const dag = buildDag(steps);
    const { valid, errors } = validateDag(dag);
    expect(valid).toBe(true);
    expect(errors).toHaveLength(0);
  });

  it('catches missing dependency', () => {
    const nodes = [
      { step: makeStep('a'), dependencies: ['ghost'] },
    ];
    const { valid, errors } = validateDag(nodes);
    expect(valid).toBe(false);
    expect(errors[0]).toContain('ghost');
  });
});

// ---------------------------------------------------------------------------
// Executor tests
// ---------------------------------------------------------------------------

describe('SopExecutor', () => {
  let executor: SopExecutor;

  beforeEach(() => {
    executor = new SopExecutor();
  });

  it('runs SOP with shell steps successfully', async () => {
    const result = parseSopYaml(MINIMAL_SOP_YAML);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    expect(run.status).toBe('success');
    expect(run.steps).toHaveLength(1);
    expect(run.steps[0].status).toBe('success');
    expect(run.steps[0].output).toBe('hello');
  });

  it('runs linear chain in correct order', async () => {
    const result = parseSopYaml(TWO_STEP_SOP_YAML);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    expect(run.status).toBe('success');
    expect(run.steps).toHaveLength(2);
  });

  it('checks env_set precondition — passes when var is set', async () => {
    process.env['TEST_PRECOND_VAR'] = 'yes';
    const yaml = `
sop:
  name: precond-test
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions:
    - type: env_set
      value: TEST_PRECOND_VAR
  steps:
    - id: s1
      name: "S1"
      action: shell
      command: "echo ok"
      on_failure: stop
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    expect(run.status).toBe('success');
    delete process.env['TEST_PRECOND_VAR'];
  });

  it('fails when precondition env_set is not met', async () => {
    delete process.env['MISSING_VAR_XYZ'];
    const yaml = `
sop:
  name: precond-fail
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions:
    - type: env_set
      value: MISSING_VAR_XYZ
      message: "MISSING_VAR_XYZ must be set"
  steps:
    - id: s1
      name: "S1"
      action: shell
      command: "echo ok"
      on_failure: stop
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    expect(run.status).toBe('failed');
    expect(run.error).toContain('MISSING_VAR_XYZ');
  });

  it('skips step when condition evaluates to false', async () => {
    const yaml = `
sop:
  name: condition-test
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions: []
  steps:
    - id: skipped
      name: "Should skip"
      action: shell
      command: "echo skipped"
      condition: "false"
      on_failure: stop
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    expect(run.status).toBe('success');
    expect(run.steps[0].status).toBe('skipped');
  });

  it('continues when step on_failure is continue', async () => {
    const yaml = `
sop:
  name: continue-test
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions: []
  steps:
    - id: fail-step
      name: "Failing step"
      action: shell
      command: "exit 1"
      on_failure: continue
    - id: after-fail
      name: "After fail"
      action: shell
      command: "echo after"
      on_failure: stop
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    // Both steps in layer 1 (no on_success chain), so fail-step runs and continues
    const failStep = run.steps.find((s) => s.stepId === 'fail-step');
    expect(failStep?.status).toBe('failed');
  });

  it('stops execution when step on_failure is stop', async () => {
    const yaml = `
sop:
  name: stop-test
  version: "1.0.0"
  tags: []
  inputs: []
  preconditions: []
  steps:
    - id: fail-stop
      name: "Fails and stops"
      action: shell
      command: "exit 1"
      on_failure: stop
      on_success: next-step
    - id: next-step
      name: "Should not run"
      action: shell
      command: "echo next"
      on_failure: stop
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value);
    expect(run.status).toBe('failed');
    // next-step should not have run since fail-stop was in layer 1 and failed with stop
  });

  it('interpolates variables from inputs', async () => {
    const yaml = `
sop:
  name: interpolate-test
  version: "1.0.0"
  tags: []
  inputs:
    - name: greeting
      type: string
      required: true
  preconditions: []
  steps:
    - id: greet
      name: "Greet"
      action: shell
      command: "echo {greeting}"
      on_failure: stop
`;
    const result = parseSopYaml(yaml);
    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const run = await executor.run(result.value, { greeting: 'world' });
    expect(run.status).toBe('success');
    expect(run.steps[0].output).toBe('world');
  });
});

// ---------------------------------------------------------------------------
// Rollback tests
// ---------------------------------------------------------------------------

describe('rollback', () => {
  it('returns success with empty completed steps', async () => {
    const result = await rollback([], []);
    expect(result.success).toBe(true);
    expect(result.rolledBack).toHaveLength(0);
  });

  it('rolls back completed steps in reverse order', async () => {
    const stepDefs = [makeStep('a'), makeStep('b'), makeStep('c')];
    const completed = [
      makeStepState('a'),
      makeStepState('b'),
      makeStepState('c'),
    ];

    const result = await rollback(completed, stepDefs);
    expect(result.success).toBe(true);
    expect(result.rolledBack).toEqual(['c', 'b', 'a']);
  });

  it('skips failed steps during rollback', async () => {
    const stepDefs = [makeStep('a'), makeStep('b')];
    const completed = [
      makeStepState('a', 'success'),
      makeStepState('b', 'failed'),
    ];

    const result = await rollback(completed, stepDefs);
    expect(result.rolledBack).toContain('a');
    expect(result.rolledBack).not.toContain('b');
  });
});

// ---------------------------------------------------------------------------
// Metrics tests
// ---------------------------------------------------------------------------

describe('collectMetrics', () => {
  it('calculates total duration and step counts', () => {
    const run = makeRun({
      steps: [
        makeStepState('s1', 'success'),
        makeStepState('s2', 'success'),
        makeStepState('s3', 'failed'),
      ],
    });

    const metrics = collectMetrics(run);
    expect(metrics.stepCount).toBe(3);
    expect(metrics.successCount).toBe(2);
    expect(metrics.failedCount).toBe(1);
    expect(metrics.totalDurationMs).toBeGreaterThanOrEqual(0);
  });

  it('returns zero averageStepDurationMs for run with no steps', () => {
    const run = makeRun({ steps: [] });
    const metrics = collectMetrics(run);
    expect(metrics.averageStepDurationMs).toBe(0);
    expect(metrics.stepCount).toBe(0);
  });
});

describe('compareRuns', () => {
  it('detects regression when current run is slower', () => {
    const prev = collectMetrics(makeRun({
      startedAt: new Date(0).toISOString(),
      completedAt: new Date(1000).toISOString(),
    }));
    const current = collectMetrics(makeRun({
      startedAt: new Date(0).toISOString(),
      completedAt: new Date(2500).toISOString(), // >20% slower
    }));

    const suggestions = compareRuns(current, prev);
    expect(suggestions.length).toBeGreaterThan(0);
    expect(suggestions[0]).toContain('longer');
  });

  it('detects new failures', () => {
    const prev = collectMetrics(makeRun({ steps: [] }));
    const current = collectMetrics(makeRun({
      steps: [makeStepState('s1', 'failed')],
    }));

    const suggestions = compareRuns(current, prev);
    expect(suggestions.some((s) => s.includes('failure') || s.includes('s1'))).toBe(true);
  });

  it('returns empty suggestions when no regressions', () => {
    const run = makeRun({
      startedAt: new Date(0).toISOString(),
      completedAt: new Date(1000).toISOString(),
      steps: [makeStepState('s1', 'success')],
    });
    const metrics = collectMetrics(run);
    const suggestions = compareRuns(metrics, metrics);
    expect(suggestions).toHaveLength(0);
  });

  it('detects increased retry count', () => {
    const prev = collectMetrics(makeRun({ steps: [] }));
    const current = collectMetrics(makeRun({
      steps: [{ ...makeStepState('s1'), retryCount: 3 }],
    }));

    const suggestions = compareRuns(current, prev);
    expect(suggestions.some((s) => s.includes('retries'))).toBe(true);
  });
});
