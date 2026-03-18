// Adapters
export { BaseAdapter } from './adapters/base-adapter.ts';
export { ClaudeCliAdapter } from './adapters/claude-cli.ts';
export { GeminiCliAdapter } from './adapters/gemini-cli.ts';
export { QwenCliAdapter } from './adapters/qwen-cli.ts';
export { BlackboxCliAdapter } from './adapters/blackbox-cli.ts';

// Types from base
export type {
  ExecOptions,
  ExecResult,
  CliState,
  AdapterHealth,
} from './adapters/base-adapter.ts';

// Discovery
export { discoverClis, getInstalledProviders } from './discovery.ts';
export type { DiscoveredCli } from './discovery.ts';

// Router
export { CliRouter } from './router.ts';
export type { RoutePreferences } from './router.ts';

// Failover
export { FailoverChain } from './failover.ts';
