import { BaseAdapter } from './adapters/base-adapter.ts';
import { ClaudeCliAdapter } from './adapters/claude-cli.ts';
import { GeminiCliAdapter } from './adapters/gemini-cli.ts';
import { QwenCliAdapter } from './adapters/qwen-cli.ts';
import { BlackboxCliAdapter } from './adapters/blackbox-cli.ts';

export interface RoutePreferences {
  /** Preferred provider names in priority order */
  preferredProviders?: string[];
  /** 'simple' | 'medium' | 'complex' — hints at compute tier needed */
  complexity?: 'simple' | 'medium' | 'complex';
  /** Skip providers whose binary is not available */
  skipUnavailable?: boolean;
}

// Default preference order: claude > gemini > qwen > blackbox
const DEFAULT_ORDER = ['claude', 'gemini', 'qwen', 'blackbox'] as const;

const ALL_ADAPTERS: BaseAdapter[] = [
  new ClaudeCliAdapter(),
  new GeminiCliAdapter(),
  new QwenCliAdapter(),
  new BlackboxCliAdapter(),
];

function adaptersByOrder(order: readonly string[]): BaseAdapter[] {
  return order
    .map((name) => ALL_ADAPTERS.find((a) => a.name === name))
    .filter((a): a is BaseAdapter => a !== undefined);
}

export class CliRouter {
  private readonly adapters: BaseAdapter[];

  constructor(adapters: BaseAdapter[] = ALL_ADAPTERS) {
    this.adapters = adapters;
  }

  route(task: string, preferences: RoutePreferences = {}): BaseAdapter {
    const order = preferences.preferredProviders ?? DEFAULT_ORDER;
    const candidates = adaptersByOrder(order);
    const skipUnavailable = preferences.skipUnavailable ?? true;

    // For simple tasks prefer lighter providers (qwen/blackbox first when reversed)
    const ranked =
      preferences.complexity === 'simple'
        ? [...candidates].reverse()
        : candidates;

    for (const adapter of ranked) {
      if (skipUnavailable && !adapter.isAvailable()) continue;
      return adapter;
    }

    // Fallback: first adapter in default order regardless of availability
    const fallback = adaptersByOrder(DEFAULT_ORDER)[0];
    if (fallback === undefined) throw new Error('No CLI adapters registered');
    return fallback;
  }

  listAvailable(): BaseAdapter[] {
    return this.adapters.filter((a) => a.isAvailable());
  }
}
