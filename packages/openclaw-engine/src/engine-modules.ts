/**
 * Type definitions for all OpenClaw Engine sub-modules.
 * Maps to JS implementations in orchestration/, intelligence/, reliability/, safety/, observability/.
 */

/** Dispatch and mission routing via orchestration layer */
export interface OrchestrationModule {
  dispatchMission(config: { goal: string; priority?: number }): Promise<{ id: string; status: string }>;
  getDispatchQueue(): Promise<Array<{ id: string; goal: string; status: string }>>;
  validateDispatch(mission: { goal: string }): Promise<boolean>;
  routeToAgent(missionId: string, agentType: string): Promise<{ routed: boolean }>;
}

/** Learning, evolution, and complexity classification */
export interface IntelligenceModule {
  classifyMissionComplexity(goal: string): Promise<string>;
  getEvolutionState(): Promise<{ level: number; score: number }>;
  getLearningInsights(): Promise<Array<{ pattern: string; confidence: number }>>;
  scanProject(rootDir: string): Promise<{ files: number; issues: string[] }>;
}

/** Circuit breaker, heartbeat, and recovery */
export interface ReliabilityModule {
  getCircuitBreakerState(): string;
  checkHeartbeat(): Promise<boolean>;
  recoverMission(id: string): Promise<{ recovered: boolean; reason: string }>;
  getSystemHealth(): Promise<{ cpu: number; memory: number; uptime: number }>;
}

/** Resource governance and safety guards */
export interface SafetyModule {
  checkResourceGovernor(): Promise<{ safe: boolean; cpuPercent: number; memoryMB: number }>;
  getSafetyGuardStatus(): boolean;
  triggerSelfHeal(issue: string): Promise<{ healed: boolean }>;
}

/** AGI scoring, rate gating, health server, mission journal */
export interface ObservabilityModule {
  getAGIScore(): Promise<number>;
  getMissionJournal(): Promise<Array<{ id: string; goal: string; result: string; timestamp: number }>>;
  getHealthMetrics(): Promise<{ uptime: number; missions: number; failRate: number }>;
  checkRateLimit(tenantId: string): Promise<{ allowed: boolean; remaining: number }>;
}

/** RaaS: tenant management, billing, rate limiting, health */
export interface RaaSModule {
  validateCommand(tenantId: string, command: string, credits: number): Promise<{ ok: boolean; status: number; remaining?: number }>;
  getBalance(tenantId: string): Promise<{ tier: string; used: number; remaining: number; limit: number }>;
  onboardTenant(req: { tenantId: string; tier: string; email: string }): Promise<{ apiKey: string; expiresAt: number }>;
  checkHealth(): Promise<{ status: string; version: string; uptime: number }>;
  checkRateLimit(tenantId: string): Promise<{ allowed: boolean; remaining: number; resetAt: number }>;
  getUsageAnalytics(tenantId: string): Promise<{ totalCalls: number; creditsUsed: number; avgLatencyMs: number }>;
}

/** Aggregated access to all engine sub-modules */
export interface EngineModules {
  orchestration: OrchestrationModule;
  intelligence: IntelligenceModule;
  reliability: ReliabilityModule;
  safety: SafetyModule;
  observability: ObservabilityModule;
  raas: RaaSModule;
}
