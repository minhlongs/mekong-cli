import { describe, it, expect, beforeEach, vi } from 'vitest';
import type { AgentDefinition, TaskAssignment } from '../../src/types/agent.js';
import type { ChatRequest } from '../../src/llm/types.js';
import { WorkerAgent, type WorkerDeps } from '../../src/agents/worker.js';
import { AgentPool } from '../../src/agents/pool.js';
import { OrchestratorAgent } from '../../src/agents/orchestrator.js';
import { executeSequential } from '../../src/agents/patterns/sequential.js';
import { executeHierarchical } from '../../src/agents/patterns/hierarchical.js';
import { executeGraph } from '../../src/agents/patterns/graph.js';
import { ToolRegistry } from '../../src/tools/registry.js';
import { SecurityManager } from '../../src/tools/security.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeMockLlm(content = 'Task completed successfully') {
  return {
    chat: vi.fn().mockResolvedValue({
      content,
      toolCalls: undefined,
      usage: { inputTokens: 100, outputTokens: 50 },
      cost: 0.001,
      model: 'test-model',
      provider: 'test',
      latencyMs: 10,
      finishReason: 'stop' as const,
    }),
    costTracker: { record: () => {}, getSummary: () => ({ totalCost: 0, totalRequests: 0, byModel: {}, byProvider: {} }) },
    getProviders: () => ['test'],
    getUsageSummary: () => ({ totalCost: 0, totalRequests: 0, byModel: {}, byProvider: {} }),
  } as unknown as WorkerDeps['llm'];
}

function makeTask(id: string, description = `Task ${id}`): TaskAssignment {
  return {
    id,
    description,
    agentId: 'agent-1',
    priority: 'normal',
    inputs: {},
    expectedOutputs: [],
    timeout: 30,
    retryCount: 0,
    maxRetries: 1,
  };
}

const baseDefinition: AgentDefinition = {
  name: 'test-agent',
  role: 'worker',
  goal: 'Complete the task',
  tools: [],
  constraints: {
    max_iterations: 10,
    max_tokens_per_turn: 4096,
    require_tests: false,
    sandbox: false,
  },
  model: { provider: 'test', model: 'test-model', temperature: 0 },
  memory: { type: 'session', max_context: 10000 },
};

function makeDeps(llm = makeMockLlm()): WorkerDeps {
  return {
    llm,
    tools: new ToolRegistry(new SecurityManager(2)),
  };
}

// ---------------------------------------------------------------------------
// WorkerAgent
// ---------------------------------------------------------------------------

describe('WorkerAgent', () => {
  it('initialises with pending status', () => {
    const agent = new WorkerAgent(baseDefinition, makeDeps());
    expect(agent.status).toBe('pending');
    expect(agent.id).toMatch(/^agent_/);
  });

  it('executes task and returns result message', async () => {
    const agent = new WorkerAgent(baseDefinition, makeDeps());
    const task = makeTask('t1', 'Write a summary');
    const msg = await agent.execute(task);

    expect(msg.type).toBe('result');
    expect(msg.from).toBe('test-agent');
    expect(msg.to).toBe('orchestrator');
    expect(msg.payload.content).toBe('Task completed successfully');
    expect(msg.payload.metadata.iterations).toBe(1);
  });

  it('sets status to success after execution', async () => {
    const agent = new WorkerAgent(baseDefinition, makeDeps());
    await agent.execute(makeTask('t2'));
    expect(agent.status).toBe('success');
  });

  it('accumulates token usage', async () => {
    const llm = makeMockLlm();
    const agent = new WorkerAgent(baseDefinition, makeDeps(llm));
    const msg = await agent.execute(makeTask('t3'));
    const usage = msg.payload.metadata.tokenUsage as { input: number; output: number };
    expect(usage.input).toBe(100);
    expect(usage.output).toBe(50);
  });

  it('stops when max_iterations exceeded', async () => {
    const def: AgentDefinition = {
      ...baseDefinition,
      constraints: { ...baseDefinition.constraints, max_iterations: 1 },
    };
    // LLM always returns tool calls to keep loop going
    const llm = {
      chat: vi.fn().mockResolvedValue({
        content: '',
        toolCalls: [{ id: 'c1', name: 'shell', arguments: { command: 'echo hi' } }],
        usage: { inputTokens: 10, outputTokens: 5 },
        cost: 0,
        model: 'test-model',
        provider: 'test',
        latencyMs: 1,
        finishReason: 'tool_calls' as const,
      }),
      costTracker: { record: () => {} },
      getProviders: () => [],
      getUsageSummary: () => ({}),
    } as unknown as WorkerDeps['llm'];

    // Register shell tool so execution doesn't fail on missing tool
    const registry = new ToolRegistry(new SecurityManager(2));
    const agent = new WorkerAgent(def, { llm, tools: registry });
    const msg = await agent.execute(makeTask('t4'));

    expect(msg.payload.content).toContain('Max iterations');
  });

  it('handles LLM error gracefully', async () => {
    const llm = {
      chat: vi.fn().mockRejectedValue(new Error('Network timeout')),
      costTracker: { record: () => {} },
      getProviders: () => [],
      getUsageSummary: () => ({}),
    } as unknown as WorkerDeps['llm'];

    // With max_iterations: 1 and an LLM that always throws, the loop sets
    // lastActionFailed=true but still tries once before constraint kicks in on iteration 2.
    const def: AgentDefinition = {
      ...baseDefinition,
      constraints: { ...baseDefinition.constraints, max_iterations: 1 },
    };
    const agent = new WorkerAgent(def, { llm, tools: new ToolRegistry(new SecurityManager(2)) });
    const msg = await agent.execute(makeTask('t5'));

    // Should have stopped — content is either LLM error or constraint violation
    expect(msg.payload.content.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// AgentPool
// ---------------------------------------------------------------------------

describe('AgentPool', () => {
  let pool: AgentPool;

  beforeEach(() => {
    pool = new AgentPool(makeDeps(), 2);
    pool.registerDefinition(baseDefinition);
  });

  it('registers definition and lists it', () => {
    expect(pool.listDefinitions()).toContain('test-agent');
  });

  it('spawns an agent from registered definition', () => {
    const agent = pool.spawn('test-agent');
    expect(agent).toBeInstanceOf(WorkerAgent);
    expect(pool.size).toBe(1);
  });

  it('throws when spawning unknown definition', () => {
    expect(() => pool.spawn('nonexistent')).toThrow('not found');
  });

  it('enforces WIP limit', async () => {
    // Spawn two agents (limit = 2), start them running so activeCount > 0
    const a1 = pool.spawn('test-agent');
    const a2 = pool.spawn('test-agent');

    // Manually trigger their execute concurrently (don't await yet)
    const t1 = a1.execute(makeTask('wip-1'));
    const t2 = a2.execute(makeTask('wip-2'));

    // While they are running, spawning a third should fail
    // (they become 'running' immediately on execute call)
    // But since execute is async and we already spawned 2, trying to spawn a 3rd
    // after size == wipLimit should throw regardless of status
    expect(() => pool.spawn('test-agent')).toThrow('WIP limit');

    await Promise.all([t1, t2]);
  });

  it('release removes agent from pool', () => {
    const agent = pool.spawn('test-agent');
    const removed = pool.release(agent.id);
    expect(removed).toBe(true);
    expect(pool.size).toBe(0);
  });

  it('release returns false for unknown id', () => {
    expect(pool.release('nonexistent')).toBe(false);
  });

  it('clear empties the pool', () => {
    pool.spawn('test-agent');
    pool.clear();
    expect(pool.size).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Sequential pattern
// ---------------------------------------------------------------------------

describe('executeSequential', () => {
  it('executes tasks in order', async () => {
    const order: string[] = [];
    const tasks = [makeTask('s1'), makeTask('s2'), makeTask('s3')];
    const deps = makeDeps();

    await executeSequential(tasks, (idx) => {
      order.push(tasks[idx].id);
      return new WorkerAgent(baseDefinition, deps);
    });

    expect(order).toEqual(['s1', 's2', 's3']);
  });

  it('passes previous output to next task input', async () => {
    const tasks = [makeTask('s1', 'first'), makeTask('s2', 'second')];
    let secondTaskInputs: Record<string, unknown> = {};

    const createWorker = (idx: number) => {
      if (idx === 1) {
        // Capture inputs of second task after chain injection
        const original = tasks[1];
        Object.defineProperty(tasks, 1, {
          get: () => {
            secondTaskInputs = original.inputs;
            return original;
          },
          configurable: true,
        });
      }
      return new WorkerAgent(baseDefinition, makeDeps());
    };

    await executeSequential(tasks, createWorker);
    // After run, second task's inputs should have previousOutput
    expect(tasks[1].inputs.previousOutput).toBe('Task completed successfully');
  });

  it('stops on error when worker throws synchronously', async () => {
    const tasks = [makeTask('e1'), makeTask('e2'), makeTask('e3')];
    let workerCallCount = 0;

    const result = await executeSequential(tasks, (idx) => {
      workerCallCount++;
      const agent = new WorkerAgent(baseDefinition, makeDeps());
      if (idx === 0) {
        // Override execute to throw — simulates a worker-level crash
        vi.spyOn(agent, 'execute').mockRejectedValue(new Error('worker crash'));
      }
      return agent;
    });

    // First task throws (caught by sequential), stops chain
    expect(result.failedCount).toBe(1);
    expect(workerCallCount).toBe(1);
    expect(result.results[0].type).toBe('error');
  });

  it('returns correct counts on success', async () => {
    const tasks = [makeTask('ok1'), makeTask('ok2')];
    const result = await executeSequential(tasks, () => new WorkerAgent(baseDefinition, makeDeps()));
    expect(result.completedCount).toBe(2);
    expect(result.failedCount).toBe(0);
    expect(result.totalDurationMs).toBeGreaterThanOrEqual(0);
  });
});

// ---------------------------------------------------------------------------
// Hierarchical pattern
// ---------------------------------------------------------------------------

describe('executeHierarchical', () => {
  it('executes all tasks and returns results', async () => {
    const tasks = [makeTask('h1'), makeTask('h2'), makeTask('h3'), makeTask('h4')];
    const result = await executeHierarchical(tasks, () => new WorkerAgent(baseDefinition, makeDeps()), 2);

    expect(result.completedCount).toBe(4);
    expect(result.failedCount).toBe(0);
    expect(result.childResults).toHaveLength(4);
  });

  it('respects WIP limit — processes in batches', async () => {
    const concurrentPeak = { value: 0 };
    let current = 0;

    const llm = {
      chat: vi.fn().mockImplementation(async (_req: ChatRequest) => {
        current++;
        concurrentPeak.value = Math.max(concurrentPeak.value, current);
        await new Promise(r => setTimeout(r, 10));
        current--;
        return {
          content: 'done',
          toolCalls: undefined,
          usage: { inputTokens: 10, outputTokens: 5 },
          cost: 0,
          model: 'test-model',
          provider: 'test',
          latencyMs: 10,
          finishReason: 'stop' as const,
        };
      }),
      costTracker: { record: () => {} },
      getProviders: () => [],
      getUsageSummary: () => ({}),
    } as unknown as WorkerDeps['llm'];

    const tasks = Array.from({ length: 6 }, (_, i) => makeTask(`h${i}`));
    await executeHierarchical(tasks, () => new WorkerAgent(baseDefinition, { llm, tools: new ToolRegistry(new SecurityManager(2)) }), 2);

    expect(concurrentPeak.value).toBeLessThanOrEqual(2);
  });

  it('captures errors without stopping other tasks', async () => {
    const tasks = [makeTask('hf1'), makeTask('hf2')];

    const result = await executeHierarchical(
      tasks,
      (idx) => {
        const agent = new WorkerAgent(baseDefinition, makeDeps());
        if (idx === 0) {
          vi.spyOn(agent, 'execute').mockRejectedValue(new Error('boom'));
        }
        return agent;
      },
      2,
    );

    expect(result.failedCount).toBe(1);
    expect(result.completedCount).toBe(1);
    expect(result.childResults[0].type).toBe('error');
    expect(result.childResults[1].type).toBe('result');
  });
});

// ---------------------------------------------------------------------------
// Graph pattern
// ---------------------------------------------------------------------------

describe('executeGraph', () => {
  it('executes independent nodes in parallel', async () => {
    const nodes = [
      { task: makeTask('g1'), dependencies: [] },
      { task: makeTask('g2'), dependencies: [] },
    ];
    const result = await executeGraph(nodes, () => new WorkerAgent(baseDefinition, makeDeps()));

    expect(result.completedCount).toBe(2);
    expect(result.failedCount).toBe(0);
    expect(result.executionOrder).toHaveLength(2);
  });

  it('respects dependency order', async () => {
    const order: string[] = [];
    const llm = {
      chat: vi.fn().mockImplementation(async (_req: ChatRequest) => {
        return {
          content: 'done',
          toolCalls: undefined,
          usage: { inputTokens: 10, outputTokens: 5 },
          cost: 0,
          model: 'test-model',
          provider: 'test',
          latencyMs: 1,
          finishReason: 'stop' as const,
        };
      }),
      costTracker: { record: () => {} },
      getProviders: () => [],
      getUsageSummary: () => ({}),
    } as unknown as WorkerDeps['llm'];

    const nodes = [
      { task: makeTask('root'), dependencies: [] },
      { task: makeTask('child'), dependencies: ['root'] },
    ];

    const result = await executeGraph(nodes, (taskId) => {
      order.push(taskId);
      return new WorkerAgent(baseDefinition, { llm, tools: new ToolRegistry(new SecurityManager(2)) });
    });

    expect(order[0]).toBe('root');
    expect(order[1]).toBe('child');
    expect(result.completedCount).toBe(2);
  });

  it('skips tasks whose dependency failed', async () => {
    const nodes = [
      { task: makeTask('fail-root'), dependencies: [] },
      { task: makeTask('skip-child'), dependencies: ['fail-root'] },
    ];

    const result = await executeGraph(
      nodes,
      (taskId) => {
        const agent = new WorkerAgent(baseDefinition, makeDeps());
        if (taskId === 'fail-root') {
          vi.spyOn(agent, 'execute').mockRejectedValue(new Error('dep-fail'));
        }
        return agent;
      },
    );

    expect(result.failedCount).toBe(2); // root failed + child skipped
    expect(result.results.get('skip-child')?.payload.content).toContain('Skipped');
  });

  it('detects circular dependencies', async () => {
    const nodes = [
      { task: makeTask('c1'), dependencies: ['c2'] },
      { task: makeTask('c2'), dependencies: ['c1'] },
    ];

    const result = await executeGraph(nodes, () => new WorkerAgent(baseDefinition, makeDeps()));

    expect(result.failedCount).toBeGreaterThan(0);
    const hasDeadlock = Array.from(result.results.values()).some(r =>
      r.payload.content.includes('Deadlock') || r.payload.content.includes('circular'),
    );
    expect(hasDeadlock).toBe(true);
  });

  it('injects dependency output into child task inputs', async () => {
    let childTaskInputs: Record<string, unknown> = {};
    const captureParentLlm = {
      chat: vi.fn().mockImplementation(async (req: ChatRequest) => {
        // Last message before the user message contains inputs
        const lastMsg = req.messages[req.messages.length - 1];
        if (lastMsg.content.includes('dep_root')) {
          childTaskInputs = { captured: lastMsg.content };
        }
        return {
          content: 'parent done',
          toolCalls: undefined,
          usage: { inputTokens: 10, outputTokens: 5 },
          cost: 0, model: 'test-model', provider: 'test', latencyMs: 1,
          finishReason: 'stop' as const,
        };
      }),
      costTracker: { record: () => {} },
      getProviders: () => [],
      getUsageSummary: () => ({}),
    } as unknown as WorkerDeps['llm'];

    const nodes = [
      { task: makeTask('root'), dependencies: [] },
      { task: makeTask('dep-consumer'), dependencies: ['root'] },
    ];

    await executeGraph(nodes, (taskId) => {
      const llm = taskId === 'dep-consumer' ? captureParentLlm : makeMockLlm();
      return new WorkerAgent(baseDefinition, { llm, tools: new ToolRegistry(new SecurityManager(2)) });
    });

    // dep_root key should have been injected into the child task inputs
    const childTask = nodes[1].task;
    expect(childTask.inputs['dep_root']).toBe('Task completed successfully');
  });
});

// ---------------------------------------------------------------------------
// OrchestratorAgent — pattern selection
// ---------------------------------------------------------------------------

describe('OrchestratorAgent — selectPattern', () => {
  let orchestrator: OrchestratorAgent;

  beforeEach(() => {
    orchestrator = new OrchestratorAgent(makeDeps());
    orchestrator.registerAgent(baseDefinition);
  });

  it('returns sequential for single task', () => {
    expect(orchestrator.selectPattern([makeTask('o1')])).toBe('sequential');
  });

  it('returns sequential for empty task list', () => {
    expect(orchestrator.selectPattern([])).toBe('sequential');
  });

  it('returns hierarchical for multiple tasks with no dependencies', () => {
    const tasks = [makeTask('o1'), makeTask('o2'), makeTask('o3')];
    expect(orchestrator.selectPattern(tasks)).toBe('hierarchical');
  });

  it('returns sequential for simple chain (linear dependencies)', () => {
    const tasks = [makeTask('o1'), makeTask('o2')];
    const deps = new Map([['o2', ['o1']]]);
    expect(orchestrator.selectPattern(tasks, deps)).toBe('sequential');
  });

  it('returns graph when dependencies have branching', () => {
    const tasks = [makeTask('o1'), makeTask('o2'), makeTask('o3')];
    // o3 depends on both o1 and o2 → branching
    const deps = new Map([['o3', ['o1', 'o2']]]);
    expect(orchestrator.selectPattern(tasks, deps)).toBe('graph');
  });
});

describe('OrchestratorAgent — plan', () => {
  it('builds a plan with correct pattern and estimates', () => {
    const orchestrator = new OrchestratorAgent(makeDeps());
    const tasks = [makeTask('p1'), makeTask('p2')];
    const plan = orchestrator.plan(tasks);

    expect(plan.pattern).toBe('hierarchical');
    expect(plan.tasks).toHaveLength(2);
    expect(plan.estimatedCost).toBeGreaterThan(0);
    expect(plan.estimatedTimeSeconds).toBeGreaterThan(0);
  });
});

describe('OrchestratorAgent — execute', () => {
  it('executes sequential plan and returns success', async () => {
    const orchestrator = new OrchestratorAgent(makeDeps());
    orchestrator.registerAgent(baseDefinition);
    const plan = orchestrator.plan([makeTask('e1')]);
    const result = await orchestrator.execute(plan, 'test-agent');

    expect(result.success).toBe(true);
    expect(result.completedCount).toBe(1);
    expect(result.pattern).toBe('sequential');
  });

  it('executes hierarchical plan for multiple tasks', async () => {
    const orchestrator = new OrchestratorAgent(makeDeps(), 5);
    orchestrator.registerAgent(baseDefinition);
    const tasks = [makeTask('e1'), makeTask('e2'), makeTask('e3')];
    const plan = orchestrator.plan(tasks);
    const result = await orchestrator.execute(plan, 'test-agent');

    expect(result.pattern).toBe('hierarchical');
    expect(result.completedCount).toBe(3);
    expect(result.success).toBe(true);
  });

  it('executes graph plan respecting dependencies', async () => {
    const orchestrator = new OrchestratorAgent(makeDeps(), 5);
    orchestrator.registerAgent(baseDefinition);
    const tasks = [makeTask('g1'), makeTask('g2'), makeTask('g3')];
    const deps = new Map([['g3', ['g1', 'g2']]]);
    const plan = orchestrator.plan(tasks, deps);
    const result = await orchestrator.execute(plan, 'test-agent');

    expect(result.pattern).toBe('graph');
    expect(result.completedCount).toBe(3);
  });
});
