import type { OptimizationConfig, AppConfig } from './config.js';

// Logger interface used across all agents
export interface Logger {
  debug(message: string, meta?: Record<string, unknown>): void;
  info(message: string, meta?: Record<string, unknown>): void;
  warn(message: string, meta?: Record<string, unknown>): void;
  error(message: string, meta?: Record<string, unknown>): void;
}

// Context passed to agents during execution
export interface AgentContext {
  config: OptimizationConfig;
  app: AppConfig;
  logger: Logger;
  metrics?: import('./metrics.js').BuildMetrics;
  optimizationResults?: import('./metrics.js').OptimizationResult[];
  changes?: string[];
}

// Result returned by agent execution
export interface AgentResult {
  success: boolean;
  data?: unknown;
  error?: Error;
  metrics?: import('./metrics.js').BuildMetrics;
}

// Base agent interface
export interface Agent {
  readonly name: string;
  execute(context: AgentContext): Promise<AgentResult>;
}

// Monitor agent - watches build performance
export interface MonitorAgent extends Agent {
  readonly name: 'monitor';
  collectMetrics(app: AppConfig): Promise<import('./metrics.js').BuildMetrics>;
  compareWithBaseline(metrics: import('./metrics.js').BuildMetrics): boolean;
}

// Optimizer agent - applies optimization strategies
export interface OptimizerAgent extends Agent {
  readonly name: 'optimizer';
  applyStrategy(
    strategy: string,
    app: AppConfig
  ): Promise<import('./metrics.js').OptimizationResult>;
  rollback(strategy: string): Promise<boolean>;
}

// Tester agent - validates optimizations
export interface TesterAgent extends Agent {
  readonly name: 'tester';
  runTests(app: AppConfig): Promise<boolean>;
  validateBuild(app: AppConfig): Promise<boolean>;
}

// Deploy agent - handles deployment of optimized builds
export interface DeployAgent extends Agent {
  readonly name: 'deploy';
  deploy(app: AppConfig, outputDir: string): Promise<boolean>;
  rollback(version: string): Promise<boolean>;
}
