export interface AgentResult {
  data: unknown;
  error?: string;
}

export abstract class BaseAgent {
  id: string;
  name: string;
  strategy?: string;

  constructor(config: { id: string; name: string; strategy?: string }) {
    this.id = config.id;
    this.name = config.name;
    this.strategy = config.strategy;
  }

  abstract execute(): Promise<AgentResult>;
}

export interface Agent {
  id: string;
  name: string;
  type: 'planner' | 'executor' | 'verifier';
}

export function createAgent(name: string, type: Agent['type']): Agent {
  return {
    id: crypto.randomUUID(),
    name,
    type,
  };
}

export class ROIScannerAgent extends BaseAgent {
  constructor() {
    super({ id: 'roi-scanner', name: 'ROI Scanner', strategy: 'standard' });
  }

  async execute(): Promise<AgentResult> {
    return { data: { roi: 5.5, token: 'ETH' } };
  }
}

import { MarketAnalyzerAgent } from './market-analyzer.js';
export { MarketAnalyzerAgent };

export function createDefaultRegistry() {
  const registry = new Map<string, BaseAgent>();

  const roiScanner = new ROIScannerAgent();
  registry.set(roiScanner.id, roiScanner);

  const marketAnalyzer = new MarketAnalyzerAgent();
  registry.set(marketAnalyzer.id, marketAnalyzer);

  return registry;
}

// --- OpenClaw Agent Definitions ---

export type { ModelPreference, AgentTool, AgentDefinition, AgentExecution } from './types.js';

import { leadHunterAgent } from './lead-hunter-agent.js';
import { contentWriterAgent } from './content-writer-agent.js';
import { supportBotAgent } from './support-bot-agent.js';
import { salesOpsAgent } from './sales-ops-agent.js';
import { monitorAgent } from './monitor-agent.js';

export { leadHunterAgent, contentWriterAgent, supportBotAgent, salesOpsAgent, monitorAgent };

import type { AgentDefinition } from './types.js';

/** Registry of all built-in OpenClaw agents, keyed by agent id */
export const AGENT_REGISTRY: Map<string, AgentDefinition> = new Map([
  [leadHunterAgent.id, leadHunterAgent],
  [contentWriterAgent.id, contentWriterAgent],
  [supportBotAgent.id, supportBotAgent],
  [salesOpsAgent.id, salesOpsAgent],
  [monitorAgent.id, monitorAgent],
]);

/** Look up a single agent definition by id */
export function getAgent(id: string): AgentDefinition | undefined {
  return AGENT_REGISTRY.get(id);
}

/** Return all registered agent definitions as an array */
export function listAgents(): AgentDefinition[] {
  return Array.from(AGENT_REGISTRY.values());
}
