// Adapters
export { BaseAdapter } from './adapters/base-adapter.js';
export { ClaudeCliAdapter } from './adapters/claude-cli.js';
export { GeminiCliAdapter } from './adapters/gemini-cli.js';
export { QwenCliAdapter } from './adapters/qwen-cli.js';
export { BlackboxCliAdapter } from './adapters/blackbox-cli.js';

// Types from base
export type {
  ExecOptions,
  ExecResult,
  CliState,
  AdapterHealth,
} from './adapters/base-adapter.js';

// Discovery
export { discoverClis, getInstalledProviders } from './discovery.js';
export type { DiscoveredCli } from './discovery.js';

// Router
export { CliRouter } from './router.js';
export type { RoutePreferences } from './router.js';

// Failover
export { FailoverChain } from './failover.js';
