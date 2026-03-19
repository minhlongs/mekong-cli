import { BaseAdapter, type ExecOptions, type ExecResult } from './adapters/base-adapter.js';

const CIRCUIT_BREAKER_THRESHOLD = 3;
const CIRCUIT_BREAKER_COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes

interface CircuitState {
  failures: number;
  openedAt: number | null; // timestamp when circuit opened, null = closed
}

export class FailoverChain {
  private readonly adapters: BaseAdapter[];
  private readonly circuits = new Map<string, CircuitState>();

  constructor(adapters: BaseAdapter[]) {
    if (adapters.length === 0) throw new Error('FailoverChain requires at least one adapter');
    this.adapters = adapters;
  }

  private getCircuit(name: string): CircuitState {
    let state = this.circuits.get(name);
    if (state === undefined) {
      state = { failures: 0, openedAt: null };
      this.circuits.set(name, state);
    }
    return state;
  }

  private isOpen(name: string): boolean {
    const state = this.getCircuit(name);
    if (state.openedAt === null) return false;
    const elapsed = Date.now() - state.openedAt;
    if (elapsed >= CIRCUIT_BREAKER_COOLDOWN_MS) {
      // Half-open: reset and allow retry
      state.failures = 0;
      state.openedAt = null;
      return false;
    }
    return true;
  }

  private recordFailure(name: string): void {
    const state = this.getCircuit(name);
    state.failures += 1;
    if (state.failures >= CIRCUIT_BREAKER_THRESHOLD) {
      state.openedAt = Date.now();
    }
  }

  private recordSuccess(name: string): void {
    const state = this.getCircuit(name);
    state.failures = 0;
    state.openedAt = null;
  }

  async execute(prompt: string, options?: ExecOptions): Promise<ExecResult> {
    const errors: string[] = [];

    for (const adapter of this.adapters) {
      if (this.isOpen(adapter.name)) {
        errors.push(`${adapter.name}: circuit open (cooling down)`);
        continue;
      }
      if (!adapter.isAvailable()) {
        errors.push(`${adapter.name}: binary not found`);
        continue;
      }

      try {
        const result = await adapter.exec(prompt, options);
        if (result.exitCode === 0) {
          this.recordSuccess(adapter.name);
          return result;
        }
        this.recordFailure(adapter.name);
        errors.push(`${adapter.name}: exit code ${result.exitCode}`);
      } catch (err) {
        this.recordFailure(adapter.name);
        errors.push(`${adapter.name}: ${err instanceof Error ? err.message : String(err)}`);
      }
    }

    throw new Error(`All adapters failed:\n${errors.join('\n')}`);
  }

  circuitStatus(): Record<string, { open: boolean; failures: number }> {
    const status: Record<string, { open: boolean; failures: number }> = {};
    for (const adapter of this.adapters) {
      const state = this.getCircuit(adapter.name);
      status[adapter.name] = { open: this.isOpen(adapter.name), failures: state.failures };
    }
    return status;
  }
}
