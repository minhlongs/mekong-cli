/**
 * MekongEngine — wires all modules together into a single runnable unit.
 */
import { loadConfig } from '../config/loader.js';
import type { MekongConfig } from '../types/config.js';
import { LlmRouter } from '../llm/router.js';
import { ToolRegistry } from '../tools/registry.js';
import { SecurityManager } from '../tools/security.js';
import { BudgetTracker } from '../constraints/budget.js';
import { SessionMemory } from '../memory/session.js';
import { OrchestratorAgent } from '../agents/orchestrator.js';
import { SopExecutor } from '../sops/executor.js';
import { parseSopFile } from '../sops/parser.js';
import { collectMetrics } from '../sops/metrics.js';
import { createShellTool } from '../tools/builtin/shell.js';
import { createFileReadTool, createFileWriteTool, createFileSearchTool } from '../tools/builtin/file-ops.js';
import { createGitTool } from '../tools/builtin/git-ops.js';
import { createHttpTool } from '../tools/builtin/http-client.js';
import { createAskUserTool } from '../tools/builtin/ask-user.js';
import { emit } from './events.js';
import { MekongError } from '../types/common.js';
import type { WorkerDeps } from '../agents/worker.js';
import type { SopRun } from '../types/sop.js';

export interface EngineOptions {
  configOverrides?: Partial<MekongConfig>;
  askUser?: (question: string) => Promise<string>;
}

export class MekongEngine {
  config!: MekongConfig;
  llm!: LlmRouter;
  tools!: ToolRegistry;
  orchestrator!: OrchestratorAgent;
  sopExecutor!: SopExecutor;
  session!: SessionMemory;
  budget!: BudgetTracker;
  private initialized = false;

  async init(options: EngineOptions = {}): Promise<void> {
    this.config = await loadConfig(options.configOverrides);

    this.llm = new LlmRouter(this.config);

    const security = new SecurityManager();
    this.tools = new ToolRegistry(security);
    this.registerBuiltinTools(options.askUser);

    this.budget = new BudgetTracker();
    this.session = new SessionMemory();

    const workerDeps: WorkerDeps = {
      llm: this.llm,
      tools: this.tools,
      budgetTracker: this.budget,
      sessionMemory: this.session,
    };

    this.orchestrator = new OrchestratorAgent(workerDeps);

    // Register default agent definition for ad-hoc tasks
    this.orchestrator.registerAgent({
      name: 'default',
      role: 'general-purpose assistant',
      goal: 'Complete the given task',
      tools: this.tools.list().map(t => t.name),
      constraints: {
        max_iterations: this.config.agents.max_iterations,
        max_tokens_per_turn: this.config.agents.max_tokens_per_turn,
        require_tests: false,
        sandbox: this.config.tools.sandbox_shell,
      },
      model: {
        provider: this.config.llm.default_provider,
        model: this.config.llm.default_model,
        temperature: 0.7,
      },
      memory: { type: 'session', max_context: 4096 },
    });

    this.sopExecutor = new SopExecutor({ tools: this.tools, askUser: options.askUser });

    this.initialized = true;
    emit('engine:started', { providers: this.llm.getProviders() });
  }

  /** Run a natural language task through the orchestrator */
  async run(input: string): Promise<string> {
    this.ensureInitialized();
    await this.session.append({ type: 'user_input', content: input });

    const task = {
      id: `task-${Date.now()}`,
      description: input,
      agentId: 'default',
      priority: 'normal' as const,
      inputs: {},
      expectedOutputs: [],
      timeout: this.config.agents.timeout_seconds,
      retryCount: 0,
      maxRetries: 3,
    };

    const plan = this.orchestrator.plan([task]);
    const result = await this.orchestrator.execute(plan, 'default');
    const content = result.results.map(r => r.payload.content).join('\n');

    await this.session.append({ type: 'agent_response', content });
    return content;
  }

  /** Run a SOP definition file */
  async runSop(filePath: string, inputs: Record<string, unknown> = {}): Promise<SopRun> {
    this.ensureInitialized();
    const parsed = await parseSopFile(filePath);
    if (!parsed.ok) throw new Error(parsed.error.message);

    const run = await this.sopExecutor.run(parsed.value, inputs);
    const metrics = collectMetrics(run);

    await this.session.append({
      type: 'agent_action',
      content: `SOP "${run.sopName}" ${run.status}: ${metrics.stepCount} steps, ${metrics.totalDurationMs}ms`,
    });

    return run;
  }

  /** Get engine status */
  getStatus() {
    return {
      initialized: this.initialized,
      providers: this.initialized ? this.llm.getProviders() : [],
      toolCount: this.initialized ? this.tools.list().length : 0,
      sessionId: this.initialized ? this.session.sessionId : null,
      usage: this.initialized ? this.llm.getUsageSummary() : null,
    };
  }

  /** Shutdown cleanly */
  async shutdown(): Promise<void> {
    emit('engine:stopped', {});
    this.initialized = false;
  }

  private registerBuiltinTools(askUser?: (q: string) => Promise<string>): void {
    this.tools.registerAll([
      createShellTool(),
      createFileReadTool(),
      createFileWriteTool(),
      createFileSearchTool(),
      createGitTool(),
      createHttpTool(),
      createAskUserTool(askUser),
    ]);
  }

  private ensureInitialized(): void {
    if (!this.initialized) {
      throw new MekongError('Engine not initialized. Call init() first.', 'ENGINE_NOT_INIT', false);
    }
  }
}
