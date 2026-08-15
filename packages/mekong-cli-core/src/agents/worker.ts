/**
 * WorkerAgent — ReAct (Reason → Act → Observe) loop agent.
 */
import type { AgentDefinition, AgentInstance, TaskAssignment, AgentMessage } from '../types/agent.js';
import type { ChatMessage, ChatResponse } from '../llm/types.js';
import type { LlmRouter } from '../llm/router.js';
import type { ToolRegistry } from '../tools/registry.js';
import { ConstraintChecker } from '../constraints/checker.js';
import { BudgetTracker, type BudgetLimits } from '../constraints/budget.js';
import { SessionMemory } from '../memory/session.js';
import { generateId } from '../utils/hash.js';
import { emit } from '../core/events.js';

export interface WorkerDeps {
  llm: LlmRouter;
  tools: ToolRegistry;
  budgetTracker?: BudgetTracker;
  sessionMemory?: SessionMemory;
}

export class WorkerAgent {
  private instance: AgentInstance;
  private definition: AgentDefinition;
  private conversationHistory: ChatMessage[] = [];
  private iterationCount = 0;
  private deps: WorkerDeps;
  private constraintChecker: ConstraintChecker;
  private startTime = 0;

  constructor(definition: AgentDefinition, deps: WorkerDeps) {
    this.definition = definition;
    this.deps = deps;
    this.constraintChecker = new ConstraintChecker();
    this.instance = {
      id: generateId('agent'),
      definition,
      status: 'pending',
      tokenUsage: { input: 0, output: 0 },
      startedAt: new Date().toISOString(),
    };
  }

  get id(): string { return this.instance.id; }
  get status(): string { return this.instance.status; }

  /** Main execution — ReAct pattern */
  async execute(task: TaskAssignment): Promise<AgentMessage> {
    this.instance.status = 'running';
    this.instance.currentTask = task;
    this.startTime = Date.now();
    this.iterationCount = 0;
    this.conversationHistory = [];

    if (this.deps.budgetTracker) {
      const limits: BudgetLimits = {
        maxCost: 1.0,
        maxTokens: 100000,
        maxTimeSeconds: task.timeout || 300,
        warnAtPercent: 80,
      };
      this.deps.budgetTracker.startTask(task.id, limits);
    }

    emit('agent:spawned', { agentId: this.instance.id, taskId: task.id });

    const systemPrompt = this.buildSystemPrompt(task);
    this.conversationHistory.push({ role: 'system', content: systemPrompt });
    this.conversationHistory.push({ role: 'user', content: task.description });

    const llmTools = this.buildLlmTools();
    let lastActionFailed = false;
    let finalContent = '';

    while (true) {
      this.iterationCount++;

      const constraint = this.checkConstraints(lastActionFailed);
      if (!constraint.ok) {
        finalContent = `Stopped: ${constraint.violation}`;
        break;
      }

      let response: ChatResponse;
      try {
        response = await this.deps.llm.chat({
          messages: this.conversationHistory,
          tools: llmTools.length > 0 ? llmTools : undefined,
          temperature: this.definition.model.temperature,
        });
      } catch (error) {
        lastActionFailed = true;
        finalContent = `LLM error: ${error instanceof Error ? error.message : String(error)}`;
        continue;
      }

      this.instance.tokenUsage.input += response.usage.inputTokens;
      this.instance.tokenUsage.output += response.usage.outputTokens;

      if (this.deps.budgetTracker) {
        this.deps.budgetTracker.recordUsage(task.id, {
          inputTokens: response.usage.inputTokens,
          outputTokens: response.usage.outputTokens,
          model: response.model,
          provider: response.provider,
        });
      }

      if (!response.toolCalls || response.toolCalls.length === 0) {
        finalContent = response.content;
        this.conversationHistory.push({ role: 'assistant', content: response.content });
        break;
      }

      this.conversationHistory.push({ role: 'assistant', content: response.content || '' });

      for (const toolCall of response.toolCalls) {
        const result = await this.deps.tools.execute(
          toolCall.name,
          toolCall.arguments,
          `agent:${this.instance.id}`,
        );

        this.conversationHistory.push({
          role: 'tool',
          content: JSON.stringify(result),
          tool_call_id: toolCall.id,
          name: toolCall.name,
        });

        lastActionFailed = !result.success;
      }

      if (this.deps.sessionMemory) {
        await this.deps.sessionMemory.append({
          type: 'agent_action',
          content: `Iteration ${this.iterationCount}: ${response.toolCalls.length} tool call(s)`,
          tokenCount: response.usage.inputTokens + response.usage.outputTokens,
        });
      }
    }

    this.instance.status = 'success';
    if (this.deps.budgetTracker) {
      this.deps.budgetTracker.endTask(task.id);
    }

    const message: AgentMessage = {
      id: generateId('msg'),
      from: this.definition.name,
      to: 'orchestrator',
      type: 'result',
      payload: {
        content: finalContent,
        metadata: {
          iterations: this.iterationCount,
          tokenUsage: { ...this.instance.tokenUsage },
          durationMs: Date.now() - this.startTime,
        },
        artifacts: [],
      },
      timestamp: new Date().toISOString(),
      priority: task.priority,
    };

    emit('agent:completed', { agentId: this.instance.id, taskId: task.id });
    return message;
  }

  private buildSystemPrompt(task: TaskAssignment): string {
    const parts: string[] = [
      `You are ${this.definition.name}, a ${this.definition.role}.`,
      `Goal: ${this.definition.goal}`,
    ];
    if (this.definition.backstory) parts.push(`Background: ${this.definition.backstory}`);
    parts.push(`Available tools: ${this.definition.tools.join(', ')}`);
    parts.push(`Constraints: max ${this.definition.constraints.max_iterations} iterations`);
    if (Object.keys(task.inputs).length > 0) {
      parts.push(`Task inputs: ${JSON.stringify(task.inputs)}`);
    }
    return parts.join('\n');
  }

  private buildLlmTools() {
    const tools = this.deps.tools.list();
    const allowedTools = this.definition.tools;
    return tools
      .filter(t => allowedTools.includes(t.name))
      .map(t => ({
        name: t.name,
        description: t.description,
        parameters: {
          type: 'object' as const,
          properties: Object.fromEntries(
            t.params.map(p => [p.name, { type: p.type, description: p.description }])
          ),
          required: t.params.filter(p => p.required).map(p => p.name),
        },
      }));
  }

  private checkConstraints(lastActionFailed: boolean): { ok: boolean; violation?: string } {
    if (this.iterationCount > this.definition.constraints.max_iterations) {
      return { ok: false, violation: `Max iterations (${this.definition.constraints.max_iterations}) exceeded` };
    }

    const result = this.constraintChecker.check({
      iteration: this.iterationCount,
      tokensUsed: this.instance.tokenUsage.input + this.instance.tokenUsage.output,
      timeElapsedSeconds: (Date.now() - this.startTime) / 1000,
      lastActionFailed,
    });

    return { ok: result.ok, violation: result.violation };
  }
}
