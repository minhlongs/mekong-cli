/**
 * Core types and interfaces for the Mekong Harness
 * Shared between mk (Mekong) and ak (Agent Kit) personas
 */

// ============================================================
// PERSONA TYPES
// ============================================================

export type Persona = 'mekong' | 'agentkit';

export interface PersonaConfig {
  name: Persona;
  displayName: string;
  commandPrefixes: string[];
  defaultModel: string;
  availableCommands: string[];
  hooks: Hook[];
}

export interface PersonaHookConfig {
  event: HookEvent;
  matcher: string;
  command: string;
  persona: Persona;
}

// ============================================================
// CONFIGURATION
// ============================================================

export interface HarnessConfig {
  configRoot: string;
  persona: Persona;
  model: string;
  llmEndpoint?: LLMEndpoint;
  hooks: Hook[];
  mcpServers: MCPServerConfig[];
  skills: Skill[];
  agents: AgentDef[];
  session: SessionConfig;
  memory: MemoryConfig;
}

export interface LLMEndpoint {
  baseUrl: string;
  apiKey: string;
  model: string;
  provider: 'anthropic' | 'openai' | 'google' | 'dashscope' | 'openrouter' | 'ollama' | 'offline';
}

export interface Hook {
  event: HookEvent;
  matcher: string;
  command: string;
  persona?: Persona | 'both';
  timeout?: number;
  critical?: boolean;
  priority?: 'pre' | 'post';
}

export type HookEvent =
  | 'PreToolUse'
  | 'PostToolUse'
  | 'SessionStart'
  | 'SessionEnd'
  | 'Stop'
  | 'SubagentStart'
  | 'SubagentStop'
  | 'UserPromptSubmit'
  | 'all';

export interface MCPServerConfig {
  name: string;
  command: string;
  args: string[];
  env?: Record<string, string>;
  enabled?: boolean;
}

export interface Skill {
  name: string;
  path: string;
  description: string;
  capabilities: string[];
  version: string;
}

export interface AgentDef {
  name: string;
  type: 'stock' | 'mekong' | 'custom';
  description: string;
  allowedPaths?: string[];
  model?: string;
}

export interface SessionConfig {
  id: string;
  workingDir: string;
  maxHistoryTokens: number;
  persistMemory: boolean;
}

export interface MemoryConfig {
  codebaseMemoryEnabled: boolean;
  graphEnabled: boolean;
  searchEnabled: boolean;
  indexPath?: string;
}

// ============================================================
// SESSION & STATE
// ============================================================

export interface SessionState {
  id: string;
  persona: Persona;
  currentPersona: Persona;
  workingDir: string;
  createdAt: string;
  updatedAt: string;
  history: HistoryEntry[];
  memory: MemoryLayer;
  contextTokens: number;
  agentInvocations: AgentInvocation[];
  hookOutputs: Record<string, any>;
  spawnedAgents: AgentInvocation[];
}

export interface HistoryEntry {
  id: string;
  timestamp: string;
  type: 'user' | 'assistant' | 'tool' | 'agent';
  content: string;
  metadata?: Record<string, any>;
  persona: Persona;
  tokens: number;
}

export interface CodebaseMemory {
  filesList: string[];
  concepts: string[];
  relationships: any[];
  graphIndexed: boolean;
  lastIndexed: string | null;
  symbols: number;
  files: number;
}

export interface ProjectMemory {
  decisions: Decision[];
  tasks: TaskRef[];
  conventions: Convention[];
  facts: ProjectFact[];
}

export interface UserPreferences {
  preferences: Record<string, any>;
  patterns: any[];
  defaultPersona: Persona;
  defaultModel: string;
  language: 'en' | 'vi' | 'both';
  autoCompact: boolean;
}

export interface ProjectFact {
  fact: string;
  source: string;
  timestamp: string;
}

export interface Decision {
  id: string;
  question: string;
  options: string[];
  chosen: string;
  rationale: string;
  timestamp: string;
}

export interface TaskRef {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  file?: string;
}

export interface Convention {
  name: string;
  description: string;
  pattern: string;
}

export interface AgentInvocation {
  id: string;
  agentType: string;
  prompt: string;
  status: 'running' | 'completed' | 'failed';
  result?: any;
  startedAt: string;
  completedAt?: string;
}

export interface MemoryLayer {
  codebase: CodebaseMemory;
  project: ProjectMemory;
  user: UserPreferences;
}

// ============================================================
// HOOK ENGINE
// ============================================================

export interface HookContext {
  event: HookEvent;
  toolName?: string;
  toolInput?: Record<string, any>;
  toolOutput?: any;
  sessionId: string;
  persona: Persona;
  cwd: string;
  env: Record<string, string>;
  hookOutputs?: Record<string, any>;
}

export interface HookResult {
  allowed: boolean;
  output?: string;
  error?: string;
  modifiedInput?: Record<string, any>;
}

// ============================================================
// COMMAND ROUTER
// ============================================================

export interface CommandDef {
  name: string;
  description: string;
  persona: Persona | 'both';
  aliases: string[];
  args: CommandArg[];
  handler: string;
}

export interface CommandArg {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array';
  required: boolean;
  description: string;
  default?: any;
}

export interface CommandRoute {
  command: CommandDef;
  args: Record<string, any>;
  persona: Persona;
  isExplicitPersona: boolean;
}

export interface RouteResult {
  matched: CommandDef | null;
  args: Record<string, any>;
  targetPersona: Persona;
  needsPersonaSwitch: boolean;
  suggestions?: string[];
}

// ============================================================
// LLM PROVIDER
// ============================================================

export interface LLMRequest {
  messages: LLMMessage[];
  model: string;
  temperature?: number;
  maxTokens?: number;
  tools?: LLMTool[];
  toolChoice?: 'auto' | 'none' | 'required';
  stream?: boolean;
  metadata?: Record<string, any>;
}

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string | LLMContent[];
  toolCalls?: LLMToolCall[];
  toolCallId?: string;
}

export interface LLMContent {
  type: 'text' | 'image' | 'tool_result';
  text?: string;
  imageUrl?: string;
  toolCallId?: string;
}

export interface LLMTool {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: Record<string, any>;
  };
}

export interface LLMToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface LLMResponse {
  id: string;
  model: string;
  choices: LLMChoice[];
  usage: LLMUsage;
}

export interface LLMChoice {
  index: number;
  message: LLMMessage;
  finishReason: 'stop' | 'length' | 'tool_calls' | 'content_filter';
}

export interface LLMUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

// ============================================================
// MCP TYPES
// ============================================================

export interface MCPServer {
  name: string;
  capabilities: MCPCapabilities;
  tools: MCPTool[];
  resources: MCPResource[];
  prompts: MCPPrompt[];
}

export interface MCPCapabilities {
  tools: boolean;
  resources: boolean;
  prompts: boolean;
}

export interface MCPTool {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

export interface MCPPrompt {
  name: string;
  description: string;
  arguments?: MCPPromptArgument[];
}

export interface MCPPromptArgument {
  name: string;
  description: string;
  required: boolean;
}

// ============================================================
// SKILL TYPES
// ============================================================

export interface SkillManifest {
  name: string;
  version: string;
  description: string;
  capabilities: SkillCapability[];
  commands: SkillCommand[];
  hooks: SkillHook[];
  dependencies: string[];
}

export interface SkillCapability {
  name: string;
  description: string;
  inputSchema: Record<string, any>;
  outputSchema: Record<string, any>;
}

export interface SkillCommand {
  name: string;
  description: string;
  handler: string;
}

export interface SkillHook {
  event: HookEvent;
  matcher: string;
  handler: string;
}