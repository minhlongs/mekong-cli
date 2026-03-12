# MEKONG-CLI IMPLEMENTATION SPEC v1.0
# Tài liệu này là blueprint hoàn chỉnh. Đọc xong → code từng module theo thứ tự.

---

## 1. PROJECT SCAFFOLD

### 1.1 Init Commands
```bash
mkdir mekong-cli && cd mekong-cli
pnpm init
pnpm add -D typescript @types/node vitest tsup turborepo
pnpm add commander yaml zod winston chalk ora inquirer eventemitter3 p-queue glob chokidar
npx tsc --init
```

### 1.2 tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### 1.3 package.json scripts
```json
{
  "name": "mekong-cli",
  "version": "0.1.0",
  "type": "module",
  "bin": { "mekong": "./dist/cli/index.js" },
  "scripts": {
    "build": "tsup src/cli/index.ts --format esm --dts",
    "dev": "tsx watch src/cli/index.ts",
    "test": "vitest run",
    "test:watch": "vitest",
    "lint": "tsc --noEmit"
  }
}
```

### 1.4 Directory Tree (tạo hết cấu trúc trước khi code)
```
mekong-cli/
├── CLAUDE.md
├── README.md
├── package.json
├── tsconfig.json
├── vitest.config.ts
├── src/
│   ├── cli/
│   │   ├── index.ts              # Entry point, Commander setup
│   │   ├── commands/
│   │   │   ├── run.ts            # `mekong run <task>`
│   │   │   ├── sop.ts            # `mekong sop <subcommand>`
│   │   │   ├── agent.ts          # `mekong agent <subcommand>`
│   │   │   ├── tool.ts           # `mekong tool <subcommand>`
│   │   │   ├── init.ts           # `mekong init`
│   │   │   ├── status.ts         # `mekong status`
│   │   │   └── config.ts         # `mekong config`
│   │   └── ui/
│   │       ├── spinner.ts        # Ora wrapper
│   │       ├── prompt.ts         # Inquirer wrapper
│   │       ├── output.ts         # Formatted output (tables, etc)
│   │       └── logger.ts         # Winston CLI logger
│   │
│   ├── core/
│   │   ├── engine.ts             # Main engine orchestrator
│   │   ├── gateway.ts            # Gateway router
│   │   ├── scheduler.ts          # Heartbeat scheduler
│   │   └── events.ts             # Global event bus
│   │
│   ├── agents/
│   │   ├── pool.ts               # Agent pool manager
│   │   ├── orchestrator.ts       # Orchestrator agent
│   │   ├── worker.ts             # Worker agent base class
│   │   ├── definitions/
│   │   │   ├── coder.yaml        # Coder agent definition
│   │   │   ├── researcher.yaml   # Researcher agent definition
│   │   │   ├── ops.yaml          # Ops agent definition
│   │   │   └── reviewer.yaml     # Code reviewer agent definition
│   │   └── patterns/
│   │       ├── hierarchical.ts   # Manager → Workers pattern
│   │       ├── sequential.ts     # Pipeline pattern (MetaGPT-style)
│   │       ├── graph.ts          # DAG workflow pattern
│   │       └── reactive.ts       # Event-driven pattern
│   │
│   ├── sops/
│   │   ├── parser.ts             # YAML SOP parser + Zod validation
│   │   ├── executor.ts           # SOP step executor
│   │   ├── dag.ts                # Build DAG from SOP dependencies
│   │   ├── rollback.ts           # Rollback handler
│   │   ├── metrics.ts            # SOP run metrics collector
│   │   └── templates/
│   │       ├── deploy.yaml
│   │       ├── code-review.yaml
│   │       ├── incident-response.yaml
│   │       ├── feature-dev.yaml
│   │       └── content-pipeline.yaml
│   │
│   ├── tools/
│   │   ├── registry.ts           # Tool registry (discover, load, validate)
│   │   ├── mcp-client.ts         # MCP protocol client
│   │   ├── builtin/
│   │   │   ├── shell.ts          # Shell execution (sandboxed)
│   │   │   ├── file-ops.ts       # File read/write/search
│   │   │   ├── git-ops.ts        # Git commands
│   │   │   ├── http-client.ts    # HTTP requests
│   │   │   ├── search.ts         # Web search
│   │   │   ├── browser.ts        # Headless browser
│   │   │   └── ask-user.ts       # Human-in-the-loop
│   │   └── security.ts           # Permission levels & approval flow
│   │
│   ├── memory/
│   │   ├── session.ts            # Session memory (JSONL append)
│   │   ├── persistent.ts         # Long-term memory (MD/JSON files)
│   │   ├── identity.ts           # SOUL.md / mekong.md parser
│   │   ├── knowledge.ts          # Entity & fact store
│   │   └── compactor.ts          # Context compaction
│   │
│   ├── llm/
│   │   ├── router.ts             # LLM provider router
│   │   ├── providers/
│   │   │   ├── anthropic.ts      # Claude API
│   │   │   ├── openai.ts         # GPT API
│   │   │   ├── deepseek.ts       # DeepSeek API
│   │   │   └── ollama.ts         # Local models
│   │   ├── cost-tracker.ts       # Token & cost tracking
│   │   └── types.ts              # Shared LLM types
│   │
│   ├── config/
│   │   ├── loader.ts             # Load mekong.yaml
│   │   ├── schema.ts             # Zod schema for config
│   │   └── defaults.ts           # Default config values
│   │
│   ├── constraints/
│   │   ├── parser.ts             # Parse mekong.md constraints
│   │   ├── checker.ts            # Runtime constraint enforcement
│   │   ├── budget.ts             # Budget tracker (tokens, cost, time)
│   │   └── escalation.ts         # Andon cord / escalation system
│   │
│   ├── types/
│   │   ├── agent.ts
│   │   ├── sop.ts
│   │   ├── tool.ts
│   │   ├── memory.ts
│   │   ├── config.ts
│   │   └── common.ts
│   │
│   └── utils/
│       ├── file.ts               # File helpers
│       ├── hash.ts               # Hashing utilities
│       ├── retry.ts              # Retry with backoff
│       └── validation.ts         # Common validators
│
├── templates/                     # Default SOP templates
│   └── (copied from src/sops/templates/ during init)
│
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## 2. TYPES (code đầu tiên — mọi module đều depend vào types)

### 2.1 src/types/common.ts
```typescript
/** Unique identifier */
export type Id = string;

/** ISO timestamp */
export type Timestamp = string;

/** Priority levels aligned with TPS urgency */
export type Priority = 'low' | 'normal' | 'high' | 'critical';

/** Execution status */
export type Status = 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'skipped';

/** Result wrapper - dùng thay vì throw cho expected errors */
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

/** Create success result */
export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

/** Create error result */
export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

/** Base error class for mekong-cli */
export class MekongError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly recoverable: boolean = true,
    public readonly context?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'MekongError';
  }
}
```

### 2.2 src/types/config.ts
```typescript
import { z } from 'zod';

/** Main configuration schema — validated by Zod */
export const ConfigSchema = z.object({
  version: z.string().default('1'),

  /** LLM provider settings */
  llm: z.object({
    default_provider: z.enum(['anthropic', 'openai', 'deepseek', 'ollama']).default('anthropic'),
    default_model: z.string().default('claude-sonnet-4-20250514'),
    providers: z.record(z.object({
      api_key: z.string().optional(),        // or env var name
      api_key_env: z.string().optional(),     // env var to read key from
      base_url: z.string().optional(),
      default_model: z.string().optional(),
    })).default({}),
  }).default({}),

  /** Agent defaults */
  agents: z.object({
    max_iterations: z.number().default(10),
    max_tokens_per_turn: z.number().default(4096),
    wip_limit: z.number().default(3),         // Kanban WIP limit
    timeout_seconds: z.number().default(300),
  }).default({}),

  /** Budget constraints — Jidoka auto-stop */
  budget: z.object({
    max_cost_per_task: z.number().default(1.0),     // USD
    max_tokens_per_task: z.number().default(100000),
    warn_at_percent: z.number().default(80),
  }).default({}),

  /** Tool permissions */
  tools: z.object({
    auto_approve_level: z.enum(['0', '1', '2', '3']).default('1'),
    sandbox_shell: z.boolean().default(true),
    allowed_directories: z.array(z.string()).default(['./']),
    blocked_commands: z.array(z.string()).default(['rm -rf /', 'sudo']),
  }).default({}),

  /** Heartbeat scheduler */
  heartbeat: z.object({
    enabled: z.boolean().default(false),
    interval_minutes: z.number().default(30),
    checklist_file: z.string().default('HEARTBEAT.md'),
  }).default({}),

  /** Memory settings */
  memory: z.object({
    session_dir: z.string().default('~/.mekong/sessions'),
    knowledge_dir: z.string().default('~/.mekong/knowledge'),
    max_session_size_mb: z.number().default(10),
    auto_compact: z.boolean().default(true),
  }).default({}),
});

export type MekongConfig = z.infer<typeof ConfigSchema>;
```

### 2.3 src/types/agent.ts
```typescript
import type { Id, Priority, Status, Timestamp } from './common.js';

/** Agent role definition — loaded from YAML */
export interface AgentDefinition {
  name: string;
  role: string;
  goal: string;
  backstory?: string;
  tools: string[];                // tool names this agent can use
  constraints: {
    max_iterations: number;
    max_tokens_per_turn: number;
    require_tests: boolean;
    sandbox: boolean;
  };
  model: {
    provider: string;
    model: string;
    temperature: number;
  };
  memory: {
    type: 'session' | 'persistent' | 'shared';
    max_context: number;
  };
}

/** Runtime agent instance */
export interface AgentInstance {
  id: Id;
  definition: AgentDefinition;
  status: Status;
  currentTask?: TaskAssignment;
  tokenUsage: { input: number; output: number };
  startedAt: Timestamp;
}

/** Task assigned to an agent */
export interface TaskAssignment {
  id: Id;
  description: string;
  parentTaskId?: Id;
  agentId: Id;
  priority: Priority;
  inputs: Record<string, unknown>;
  expectedOutputs: string[];
  timeout: number;                // seconds
  retryCount: number;
  maxRetries: number;
}

/** Message between agents */
export interface AgentMessage {
  id: Id;
  from: string;
  to: string;                     // agent name or 'broadcast' or 'user'
  type: 'task' | 'result' | 'query' | 'error' | 'status';
  payload: {
    content: string;
    metadata: Record<string, unknown>;
    artifacts: string[];          // file paths
  };
  timestamp: Timestamp;
  parentId?: Id;
  priority: Priority;
}

/** Orchestration pattern selection */
export type OrchestrationPattern = 'hierarchical' | 'sequential' | 'graph' | 'reactive';
```

### 2.4 src/types/sop.ts
```typescript
import type { Id, Status, Timestamp } from './common.js';
import { z } from 'zod';

/** SOP input parameter */
export const SopInputSchema = z.object({
  name: z.string(),
  type: z.enum(['string', 'number', 'boolean', 'enum', 'path']),
  description: z.string().optional(),
  required: z.boolean().default(true),
  default: z.unknown().optional(),
  options: z.array(z.string()).optional(),       // for enum type
});

/** SOP precondition check */
export const SopPreconditionSchema = z.object({
  check: z.string(),               // command or expression
  expect: z.enum(['empty', 'not_empty', 'exit_code_0', 'contains', 'status_200']),
  value: z.string().optional(),     // for 'contains' check
  message: z.string(),             // error message if fails
});

/** SOP step definition */
export const SopStepSchema = z.object({
  id: z.string(),
  name: z.string(),
  agent: z.string().default('default'),
  action: z.enum(['shell', 'llm', 'webhook', 'file', 'prompt', 'composite']),
  command: z.string().optional(),
  config: z.record(z.unknown()).optional(),
  timeout: z.string().default('300s'),
  depends_on: z.array(z.string()).default([]),
  parallel_with: z.array(z.string()).default([]),
  on_failure: z.enum(['abort', 'skip', 'retry', 'rollback']).default('abort'),
  retry: z.number().default(0),
  retry_delay: z.string().default('5s'),
  requires_approval: z.string().optional(),      // condition expression
  condition: z.string().optional(),               // skip-if expression
});

/** Complete SOP definition */
export const SopDefinitionSchema = z.object({
  sop: z.object({
    name: z.string(),
    version: z.string().default('1.0.0'),
    author: z.string().optional(),
    category: z.string().optional(),
    description: z.string().optional(),
    estimated_time: z.string().optional(),
    inputs: z.array(SopInputSchema).default([]),
    preconditions: z.array(SopPreconditionSchema).default([]),
    steps: z.array(SopStepSchema).min(1),
    postconditions: z.array(SopPreconditionSchema).default([]),
    rollback: z.object({
      trigger: z.string().optional(),
      steps: z.array(SopStepSchema).default([]),
    }).optional(),
    metrics: z.object({
      track: z.array(z.string()).default(['total_time', 'step_times']),
      compare_with: z.string().default('last_10_runs'),
      alert_if: z.string().optional(),
    }).optional(),
  }),
});

export type SopDefinition = z.infer<typeof SopDefinitionSchema>;
export type SopStep = z.infer<typeof SopStepSchema>;
export type SopInput = z.infer<typeof SopInputSchema>;

/** Runtime SOP execution state */
export interface SopRun {
  id: Id;
  sopName: string;
  sopVersion: string;
  status: Status;
  inputs: Record<string, unknown>;
  stepStates: Map<string, StepState>;
  startedAt: Timestamp;
  completedAt?: Timestamp;
  totalTokens: number;
  totalCost: number;
  error?: string;
}

export interface StepState {
  stepId: string;
  status: Status;
  startedAt?: Timestamp;
  completedAt?: Timestamp;
  output?: string;
  error?: string;
  retryCount: number;
  duration?: number;     // ms
}
```

### 2.5 src/types/tool.ts
```typescript
import { z } from 'zod';

/** Security level — Jidoka-based permission tiers */
export type SecurityLevel = 0 | 1 | 2 | 3;

/** Tool input parameter definition */
export const ToolParamSchema = z.object({
  name: z.string(),
  type: z.enum(['string', 'number', 'boolean', 'object', 'array']),
  description: z.string(),
  required: z.boolean().default(true),
  default: z.unknown().optional(),
  enum: z.array(z.string()).optional(),
});

/** Tool definition — for registry */
export interface ToolDefinition {
  name: string;
  description: string;
  category: 'builtin' | 'mcp' | 'custom';
  securityLevel: SecurityLevel;
  inputs: Array<z.infer<typeof ToolParamSchema>>;
  execute: (params: Record<string, unknown>) => Promise<ToolResult>;
}

/** Tool execution result */
export interface ToolResult {
  success: boolean;
  output: string;
  artifacts?: string[];           // file paths created
  metadata?: Record<string, unknown>;
  error?: string;
  tokensUsed?: number;
  durationMs?: number;
}
```

### 2.6 src/types/memory.ts
```typescript
import type { Id, Timestamp } from './common.js';

/** Session log entry — appended to JSONL file */
export interface SessionEntry {
  id: Id;
  timestamp: Timestamp;
  type: 'user_input' | 'agent_action' | 'tool_call' | 'tool_result' | 'agent_response' | 'error' | 'system';
  agent?: string;
  content: string;
  metadata?: Record<string, unknown>;
  tokenCount?: number;
}

/** Knowledge entity */
export interface KnowledgeEntity {
  id: Id;
  name: string;
  type: 'person' | 'project' | 'tool' | 'concept' | 'preference' | 'fact';
  attributes: Record<string, unknown>;
  source: string;                 // which session learned this
  confidence: number;             // 0-1
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

/** Identity config — parsed from SOUL.md / mekong.md */
export interface IdentityConfig {
  name: string;
  personality: string;
  boundaries: string[];           // NEVER do X
  scopeControls: {
    wipLimit: number;
    maxTaskDepth: number;
    maxTokensPerTurn: number;
    timeLimit: number;
  };
  qualityGates: string[];         // must-do rules
  escalationProtocol: Record<string, string>;  // trigger → action
  communicationStyle: string[];
}

/** Improvement suggestion — from Kaizen loop */
export interface KaizenSuggestion {
  id: Id;
  type: 'sop_optimization' | 'tool_suggestion' | 'prompt_refinement' | 'skill_creation';
  description: string;
  evidence: string;               // metrics that support this
  estimatedImpact: 'low' | 'medium' | 'high';
  status: 'proposed' | 'approved' | 'applied' | 'rejected';
  createdAt: Timestamp;
}
```

---

## 3. MODULE IMPLEMENTATION ORDER

**Code theo đúng thứ tự này. Mỗi module depend vào modules phía trên nó.**

```
LAYER 0: Types + Utils (no dependencies)
  ├── src/types/*.ts          ← CODE THESE FIRST (spec ở trên)
  ├── src/utils/file.ts
  ├── src/utils/hash.ts
  ├── src/utils/retry.ts
  └── src/utils/validation.ts

LAYER 1: Config + Events (depends on types)
  ├── src/config/schema.ts    ← already defined in types/config.ts
  ├── src/config/defaults.ts
  ├── src/config/loader.ts    ← load mekong.yaml, merge with defaults, validate
  └── src/core/events.ts      ← EventEmitter3 global event bus

LAYER 2: Memory + Constraints (depends on config)
  ├── src/memory/session.ts
  ├── src/memory/persistent.ts
  ├── src/memory/identity.ts
  ├── src/memory/knowledge.ts
  ├── src/constraints/parser.ts
  ├── src/constraints/budget.ts
  └── src/constraints/checker.ts

LAYER 3: LLM Router (depends on config)
  ├── src/llm/types.ts
  ├── src/llm/providers/anthropic.ts
  ├── src/llm/providers/openai.ts
  ├── src/llm/providers/deepseek.ts
  ├── src/llm/providers/ollama.ts
  ├── src/llm/cost-tracker.ts
  └── src/llm/router.ts

LAYER 4: Tools (depends on llm, constraints)
  ├── src/tools/security.ts
  ├── src/tools/builtin/shell.ts
  ├── src/tools/builtin/file-ops.ts
  ├── src/tools/builtin/git-ops.ts
  ├── src/tools/builtin/http-client.ts
  ├── src/tools/builtin/ask-user.ts
  ├── src/tools/builtin/search.ts
  ├── src/tools/mcp-client.ts
  └── src/tools/registry.ts

LAYER 5: Agents (depends on tools, llm, memory)
  ├── src/agents/worker.ts
  ├── src/agents/orchestrator.ts
  ├── src/agents/patterns/hierarchical.ts
  ├── src/agents/patterns/sequential.ts
  ├── src/agents/patterns/graph.ts
  └── src/agents/pool.ts

LAYER 6: SOP Engine (depends on agents, tools)
  ├── src/sops/parser.ts
  ├── src/sops/dag.ts
  ├── src/sops/executor.ts
  ├── src/sops/rollback.ts
  ├── src/sops/metrics.ts
  └── src/sops/templates/*.yaml

LAYER 7: Core Engine (depends on everything)
  ├── src/core/gateway.ts
  ├── src/core/scheduler.ts
  └── src/core/engine.ts

LAYER 8: CLI (thin wrapper around engine)
  ├── src/cli/ui/*.ts
  ├── src/cli/commands/*.ts
  └── src/cli/index.ts
```

---

## 4. KEY MODULE SPECS

### 4.1 src/config/loader.ts
```typescript
/**
 * Load configuration from multiple sources with priority:
 * 1. CLI flags (highest)
 * 2. Environment variables (MEKONG_*)
 * 3. Project-level: ./mekong.yaml
 * 4. User-level: ~/.mekong/config.yaml
 * 5. Defaults (lowest)
 *
 * Usage:
 *   const config = await loadConfig({ cliOverrides });
 */

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { parse as parseYaml } from 'yaml';
import { ConfigSchema, type MekongConfig } from '../types/config.js';

export async function loadConfig(
  overrides?: Partial<MekongConfig>
): Promise<MekongConfig> {
  // 1. Try project-level config
  // 2. Try user-level config
  // 3. Merge with defaults
  // 4. Apply env vars (MEKONG_LLM_DEFAULT_PROVIDER, etc)
  // 5. Apply CLI overrides
  // 6. Validate with Zod
  // 7. Resolve api_key_env → actual key from env
  // Implementation: ...
}
```

### 4.2 src/core/events.ts
```typescript
/**
 * Global event bus — all modules communicate through this.
 * Events follow pattern: "module:action"
 *
 * Core events:
 *   'engine:started' | 'engine:stopped'
 *   'agent:spawned' | 'agent:completed' | 'agent:failed'
 *   'task:created' | 'task:started' | 'task:completed' | 'task:failed'
 *   'tool:called' | 'tool:result'
 *   'sop:started' | 'sop:step_completed' | 'sop:completed' | 'sop:failed'
 *   'budget:warning' | 'budget:exceeded'
 *   'constraint:violation'
 *   'memory:saved' | 'memory:compacted'
 */

import EventEmitter from 'eventemitter3';

export const eventBus = new EventEmitter();

// Type-safe event emitter wrapper
export function emit(event: string, data?: unknown): void {
  eventBus.emit(event, data);
}

export function on(event: string, handler: (data?: unknown) => void): void {
  eventBus.on(event, handler);
}
```

### 4.3 src/llm/router.ts
```typescript
/**
 * LLM Router — routes requests to the best/cheapest/configured provider.
 *
 * Features:
 * - Multi-provider support (Anthropic, OpenAI, DeepSeek, Ollama)
 * - Automatic fallback if primary provider fails
 * - Cost tracking per request
 * - Rate limiting awareness
 *
 * Usage:
 *   const router = new LlmRouter(config);
 *   const response = await router.chat({
 *     messages: [...],
 *     model: 'auto',        // router picks best model
 *     maxTokens: 4096,
 *     tools: [...],         // for function calling
 *   });
 */

export interface ChatRequest {
  messages: Array<{ role: 'system' | 'user' | 'assistant'; content: string }>;
  model?: string;              // specific model or 'auto'
  provider?: string;           // specific provider or auto-route
  maxTokens?: number;
  temperature?: number;
  tools?: ToolDefinition[];    // for function calling
  systemPrompt?: string;
}

export interface ChatResponse {
  content: string;
  toolCalls?: Array<{ name: string; arguments: Record<string, unknown> }>;
  usage: { inputTokens: number; outputTokens: number };
  cost: number;                // estimated USD cost
  model: string;
  provider: string;
  latencyMs: number;
}

export class LlmRouter {
  // Implementation: provider registry, routing logic, fallback chain
}
```

### 4.4 src/agents/worker.ts
```typescript
/**
 * Worker Agent — base class for all agents.
 * Implements ReAct (Reason → Act → Observe) loop.
 *
 * Lifecycle:
 * 1. Receive TaskAssignment
 * 2. Load relevant memory/context
 * 3. ReAct loop until task done or limits hit
 * 4. Return result + update memory
 *
 * Jidoka rules:
 * - Stop after maxRetries consecutive failures
 * - Stop if budget exceeded
 * - Stop if constraint violated
 * - Escalate to orchestrator on ambiguity
 */

import type { AgentDefinition, AgentInstance, TaskAssignment, AgentMessage } from '../types/agent.js';
import type { ToolResult } from '../types/tool.js';

export class WorkerAgent {
  private instance: AgentInstance;
  private conversationHistory: AgentMessage[];
  private iterationCount: number;

  constructor(definition: AgentDefinition) { /* ... */ }

  /** Main execution loop — ReAct pattern */
  async execute(task: TaskAssignment): Promise<AgentMessage> {
    // 1. Build system prompt from definition + identity + constraints
    // 2. Add task description + relevant memory
    // 3. LOOP:
    //    a. REASON: Call LLM with current context
    //    b. ACT: If LLM wants to use tool → execute via ToolRegistry
    //    c. OBSERVE: Add tool result to context
    //    d. CHECK: Budget? Iterations? Constraints?
    //    e. If done or limit hit → break
    // 4. Return final result as AgentMessage
    // 5. Save to session memory
    throw new Error('Not implemented');
  }

  /** Build system prompt combining role + constraints */
  private buildSystemPrompt(): string { /* ... */ return ''; }

  /** Check all constraints before each iteration — Jidoka */
  private checkConstraints(): { ok: boolean; violation?: string } { /* ... */ return { ok: true }; }
}
```

### 4.5 src/agents/orchestrator.ts
```typescript
/**
 * Orchestrator Agent — decomposes complex tasks and manages worker agents.
 *
 * Pattern selection logic:
 * - Simple task (1 step, 1 tool) → direct execution, no workers
 * - Multi-step task → hierarchical (spawn workers)
 * - SOP execution → sequential pipeline
 * - Complex with dependencies → graph-based DAG
 * - Event-driven → reactive pattern
 *
 * Kanban WIP:
 * - Never spawn more workers than wip_limit
 * - Queue excess tasks
 * - Pull model: workers pull next task when ready
 */

import type { OrchestrationPattern, TaskAssignment } from '../types/agent.js';

export class OrchestratorAgent {
  /** Analyze task and decide orchestration pattern */
  async plan(userInput: string): Promise<{
    pattern: OrchestrationPattern;
    tasks: TaskAssignment[];
    estimatedCost: number;
    estimatedTime: number;
  }> {
    // 1. Call LLM to decompose task
    // 2. Identify dependencies between subtasks
    // 3. Select pattern based on dependency graph shape
    // 4. Estimate cost and time
    // 5. Return plan for user approval (if complex)
    throw new Error('Not implemented');
  }

  /** Execute plan using selected pattern */
  async execute(plan: {
    pattern: OrchestrationPattern;
    tasks: TaskAssignment[];
  }): Promise<string> {
    // Delegate to pattern-specific executor
    throw new Error('Not implemented');
  }
}
```

### 4.6 src/sops/executor.ts
```typescript
/**
 * SOP Executor — runs SOP definitions step by step.
 *
 * Flow:
 * 1. Parse SOP YAML → validate with Zod
 * 2. Resolve inputs (prompt user for required params)
 * 3. Check preconditions
 * 4. Build DAG from step dependencies
 * 5. Execute DAG:
 *    - Sequential steps: run in order
 *    - Parallel groups: run concurrently (respecting WIP limit)
 *    - Approval gates: pause and ask user
 *    - On failure: retry, skip, abort, or trigger rollback
 * 6. Check postconditions
 * 7. Record metrics
 * 8. Kaizen: compare with historical runs, suggest improvements
 *
 * Variable interpolation:
 *   {input_name} → resolved from user inputs
 *   {env.VAR_NAME} → from environment
 *   {step.STEP_ID.output} → from previous step output
 */

import type { SopDefinition, SopRun, StepState } from '../types/sop.js';

export class SopExecutor {
  async run(sop: SopDefinition, userInputs: Record<string, unknown>): Promise<SopRun> {
    // Implementation follows the flow above
    throw new Error('Not implemented');
  }

  /** Interpolate variables in command strings */
  private interpolate(template: string, context: Record<string, unknown>): string {
    return template.replace(/\{([^}]+)\}/g, (_, key) => {
      // resolve key from context
      return String(context[key] ?? `{${key}}`);
    });
  }
}
```

### 4.7 src/tools/security.ts
```typescript
/**
 * Security permission system — 4 levels based on Jidoka principle.
 *
 * Level 0 (Safe): Auto-approved, no side effects
 *   → file_read, search, http_get (public)
 *
 * Level 1 (Moderate): Auto-approved with logging
 *   → file_write (project dir), git_commit, db_read
 *
 * Level 2 (Sensitive): Ask first time, remember preference
 *   → http_post, send_message, create_issue, api_calls
 *
 * Level 3 (Critical): ALWAYS ask — Andon cord
 *   → deploy_production, delete_*, payment_*, sudo
 */

import type { SecurityLevel } from '../types/tool.js';

export class SecurityManager {
  private approvals: Map<string, boolean> = new Map();  // tool:context → approved

  /** Check if tool execution is allowed */
  async checkPermission(
    toolName: string,
    level: SecurityLevel,
    context: string
  ): Promise<{ allowed: boolean; reason?: string }> {
    // Level 0: always allow
    // Level 1: allow + log
    // Level 2: check cache, ask if first time
    // Level 3: always ask
    throw new Error('Not implemented');
  }
}
```

### 4.8 src/constraints/budget.ts
```typescript
/**
 * Budget Tracker — enforces cost/token/time limits per task.
 * Emits 'budget:warning' at warn_at_percent and 'budget:exceeded' at 100%.
 *
 * Tracks:
 * - Total tokens (input + output) per task
 * - Estimated cost per task (using model-specific pricing)
 * - Wall clock time per task
 * - API call count per task
 *
 * Pricing (approximate, configurable):
 *   claude-sonnet-4: $3/MTok input, $15/MTok output
 *   gpt-4o: $2.50/MTok input, $10/MTok output
 *   deepseek-chat: $0.14/MTok input, $0.28/MTok output
 *   ollama: $0 (local)
 */

export class BudgetTracker {
  private taskBudgets: Map<string, TaskBudget> = new Map();

  startTask(taskId: string, limits: BudgetLimits): void { /* ... */ }
  recordUsage(taskId: string, usage: TokenUsage): void { /* ... */ }
  checkBudget(taskId: string): BudgetStatus { /* ... */ return {} as BudgetStatus; }
  getReport(taskId: string): BudgetReport { /* ... */ return {} as BudgetReport; }
}

interface BudgetLimits {
  maxCost: number;
  maxTokens: number;
  maxTimeSeconds: number;
  warnAtPercent: number;
}

interface TokenUsage {
  inputTokens: number;
  outputTokens: number;
  model: string;
  provider: string;
}

interface BudgetStatus {
  withinLimits: boolean;
  costUsed: number;
  costLimit: number;
  costPercent: number;
  tokensUsed: number;
  tokensLimit: number;
  timeUsedSeconds: number;
  timeLimit: number;
}

interface BudgetReport extends BudgetStatus {
  breakdown: Array<{
    model: string;
    calls: number;
    inputTokens: number;
    outputTokens: number;
    cost: number;
  }>;
}
```

### 4.9 src/cli/index.ts — Entry Point
```typescript
#!/usr/bin/env node

/**
 * mekong-cli entry point.
 *
 * Commands:
 *   mekong run <task>              Run a natural language task
 *   mekong sop run <name>          Execute an SOP
 *   mekong sop list                List available SOPs
 *   mekong sop create              Create new SOP interactively
 *   mekong agent list              List configured agents
 *   mekong tool list               List available tools
 *   mekong tool add <url>          Add MCP tool server
 *   mekong init                    Initialize mekong in project
 *   mekong status                  Show Andon dashboard
 *   mekong config                  View/edit configuration
 */

import { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { MekongEngine } from '../core/engine.js';

const program = new Command();

program
  .name('mekong')
  .description('Agentic CLI for one-person companies — Executable SOPs')
  .version('0.1.0');

program
  .command('run <task...>')
  .description('Run a natural language task')
  .option('-m, --model <model>', 'LLM model to use')
  .option('-p, --pattern <pattern>', 'Orchestration pattern', 'auto')
  .option('--dry-run', 'Show plan without executing')
  .option('--budget <amount>', 'Max cost in USD', '1.0')
  .action(async (taskParts: string[], opts) => {
    const config = await loadConfig();
    const engine = new MekongEngine(config);
    const task = taskParts.join(' ');
    await engine.run(task, opts);
  });

// ... more commands

program.parse();
```

---

## 5. SOP TEMPLATES (5 templates khởi điểm)

### 5.1 templates/deploy.yaml — đã có đầy đủ trong super prompt

### 5.2 templates/code-review.yaml
```yaml
sop:
  name: "Automated Code Review"
  version: "1.0.0"
  category: development
  estimated_time: "5min"

  inputs:
    - name: branch
      type: string
      required: true
    - name: base_branch
      type: string
      default: main

  preconditions:
    - check: "git rev-parse --verify {branch}"
      expect: exit_code_0
      message: "Branch {branch} must exist"

  steps:
    - id: diff
      name: "Get changes"
      action: shell
      command: "git diff {base_branch}...{branch} --stat && git diff {base_branch}...{branch}"

    - id: review
      name: "AI code review"
      agent: reviewer
      action: llm
      config:
        prompt: |
          Review this diff. Focus on:
          1. Bugs and logic errors
          2. Security issues
          3. Performance concerns
          4. Code style violations
          5. Missing tests
          Give actionable feedback with line references.
        input_from: "step.diff.output"
      depends_on: [diff]

    - id: report
      name: "Generate report"
      action: file
      config:
        path: "./review-{branch}.md"
        content_from: "step.review.output"
      depends_on: [review]
```

### 5.3 templates/feature-dev.yaml
```yaml
sop:
  name: "Feature Development Lifecycle"
  version: "1.0.0"
  category: development
  estimated_time: "30min"

  inputs:
    - name: feature
      type: string
      required: true
      description: "Feature description"
    - name: branch_prefix
      type: string
      default: "feat"

  steps:
    - id: plan
      name: "Create implementation plan"
      agent: coder
      action: llm
      config:
        prompt: |
          Create an implementation plan for: {feature}
          Include: files to modify, new files needed, test plan.
          Format as checklist.

    - id: branch
      name: "Create feature branch"
      action: shell
      command: "git checkout -b {branch_prefix}/$(echo '{feature}' | tr ' ' '-' | tr '[:upper:]' '[:lower:]' | head -c 50)"
      depends_on: [plan]

    - id: implement
      name: "Implement feature"
      agent: coder
      action: llm
      config:
        prompt: |
          Implement the feature based on this plan:
          {step.plan.output}
          
          Write the actual code. Create/modify files as needed.
      depends_on: [branch]

    - id: test
      name: "Write and run tests"
      agent: coder
      action: llm
      config:
        prompt: |
          Write tests for the feature implementation.
          Then run them. Fix any failures.
      depends_on: [implement]

    - id: commit
      name: "Commit changes"
      action: shell
      command: "git add -A && git commit -m 'feat: {feature}'"
      depends_on: [test]
      requires_approval: "true"
```

### 5.4 templates/content-pipeline.yaml
```yaml
sop:
  name: "Content Creation Pipeline"
  version: "1.0.0"
  category: business
  estimated_time: "20min"

  inputs:
    - name: topic
      type: string
      required: true
    - name: format
      type: enum
      options: [blog, social, newsletter, documentation]
      default: blog
    - name: tone
      type: enum
      options: [professional, casual, technical, storytelling]
      default: professional

  steps:
    - id: research
      name: "Research topic"
      agent: researcher
      action: llm
      config:
        prompt: |
          Research the topic: {topic}
          Find key points, recent developments, data/statistics.
          Summarize in structured outline.

    - id: draft
      name: "Write first draft"
      agent: coder
      action: llm
      config:
        prompt: |
          Write a {format} post about: {topic}
          Tone: {tone}
          Based on research: {step.research.output}
          Length: 800-1200 words for blog, 280 chars for social.
      depends_on: [research]

    - id: review
      name: "Edit and refine"
      agent: reviewer
      action: llm
      config:
        prompt: |
          Edit this draft for clarity, grammar, and engagement:
          {step.draft.output}
          Fix issues and return the improved version.
      depends_on: [draft]

    - id: save
      name: "Save final version"
      action: file
      config:
        path: "./content/{topic}-{format}.md"
        content_from: "step.review.output"
      depends_on: [review]
```

### 5.5 templates/incident-response.yaml
```yaml
sop:
  name: "Incident Response"
  version: "1.0.0"
  category: devops
  estimated_time: "varies"

  inputs:
    - name: severity
      type: enum
      options: [p0, p1, p2, p3]
      required: true
    - name: description
      type: string
      required: true
    - name: service
      type: string
      required: true

  steps:
    - id: assess
      name: "Initial assessment"
      agent: ops
      action: shell
      command: |
        echo "=== Service Health ==="
        curl -sf https://{service}/health || echo "HEALTH CHECK FAILED"
        echo "=== Recent Logs ==="
        # kubectl logs deployment/{service} --tail=50 2>/dev/null || echo "No k8s access"
        echo "=== System Resources ==="
        # kubectl top pods -l app={service} 2>/dev/null || echo "No k8s access"

    - id: diagnose
      name: "AI-assisted diagnosis"
      agent: ops
      action: llm
      config:
        prompt: |
          Incident: {description}
          Severity: {severity}
          Service: {service}
          
          Health check output: {step.assess.output}
          
          Diagnose the likely root cause and suggest immediate fix.
      depends_on: [assess]

    - id: notify
      name: "Send alert"
      action: webhook
      config:
        url: "{slack_webhook}"
        body: |
          🚨 *{severity} Incident* — {service}
          {description}
          Diagnosis: {step.diagnose.output}
      parallel_with: [fix]
      depends_on: [diagnose]

    - id: fix
      name: "Apply fix"
      agent: ops
      action: llm
      config:
        prompt: |
          Based on diagnosis: {step.diagnose.output}
          Generate and execute the fix command.
          IMPORTANT: Show the command first, wait for approval before executing.
      depends_on: [diagnose]
      requires_approval: "severity == p0"

    - id: verify
      name: "Verify fix"
      action: shell
      command: "curl -sf https://{service}/health"
      depends_on: [fix]
      retry: 5
      retry_delay: "10s"
```

---

## 6. MEKONG.YAML DEFAULT CONFIG

```yaml
# mekong.yaml — Project configuration
version: "1"

llm:
  default_provider: anthropic
  default_model: claude-sonnet-4-20250514
  providers:
    anthropic:
      api_key_env: ANTHROPIC_API_KEY
    openai:
      api_key_env: OPENAI_API_KEY
    deepseek:
      api_key_env: DEEPSEEK_API_KEY
      base_url: https://api.deepseek.com
    ollama:
      base_url: http://localhost:11434

agents:
  max_iterations: 10
  max_tokens_per_turn: 4096
  wip_limit: 3
  timeout_seconds: 300

budget:
  max_cost_per_task: 1.0
  max_tokens_per_task: 100000
  warn_at_percent: 80

tools:
  auto_approve_level: "1"
  sandbox_shell: true
  allowed_directories:
    - "./"
  blocked_commands:
    - "rm -rf /"
    - "sudo"
    - "chmod 777"

heartbeat:
  enabled: false
  interval_minutes: 30
  checklist_file: HEARTBEAT.md

memory:
  session_dir: ~/.mekong/sessions
  knowledge_dir: ~/.mekong/knowledge
  max_session_size_mb: 10
  auto_compact: true
```

---

## 7. VITEST CONFIG

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts', 'tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['src/types/**', 'dist/**'],
    },
    testTimeout: 30000,
  },
});
```

---

## 8. README SKELETON

```markdown
# mekong-cli 🌊

> Agentic CLI for one-person companies — Executable SOPs powered by multi-agent orchestration.

## What is mekong-cli?

Every SOP platform helps you **document** procedures.
mekong-cli **executes** them.

\`\`\`bash
# Run a natural language task
mekong run "review the code on branch feature/auth and create a PR"

# Execute a predefined SOP
mekong sop run deploy --environment staging --branch main

# See what's happening (Andon dashboard)
mekong status
\`\`\`

## Quick Start

\`\`\`bash
npm install -g mekong-cli
mekong init
export ANTHROPIC_API_KEY=your-key
mekong run "hello world"
\`\`\`

## Features

- 🤖 **Multi-agent orchestration** — Agents collaborate on complex tasks
- 📋 **Executable SOPs** — YAML-defined workflows that actually run
- 🔧 **MCP-compatible tools** — Extensible tool ecosystem
- 🧠 **Persistent memory** — Agents learn from past interactions
- ⏱️ **Heartbeat scheduler** — Autonomous background tasks
- 🏭 **TPS-inspired** — Jidoka, Kanban, Kaizen built into the core

## Documentation

- [Architecture](docs/architecture.md)
- [SOP Authoring Guide](docs/sop-guide.md)
- [Agent Configuration](docs/agents.md)
- [Tool Development](docs/tools.md)

## License

MIT
\`\`\`
```

---

## IMPLEMENTATION NOTES CHO OPUS

1. **BẮT ĐẦU từ scaffold**: Tạo folder structure + package.json + tsconfig TRƯỚC
2. **Code types TRƯỚC**: Tất cả modules đều import từ types/
3. **Test mỗi module**: Viết test ngay sau khi code xong module, ĐỪNG để cuối
4. **KHÔNG code browser.ts và mcp-client.ts ở phase đầu**: Đánh dấu TODO, implement sau
5. **Focus vào happy path trước**: Error handling có thể enhance sau
6. **SOP templates là YAML files**: Chỉ cần copy vào templates/, không cần code
7. **CLI entry point code CUỐI CÙNG**: Vì nó wrap tất cả modules khác
