export type SwarmTask = {
  id: string;
  type: 'code' | 'research' | 'quick' | 'review';
  prompt: string;
  priority: number;
};

export type SwarmResult = {
  taskId: string;
  provider: string;
  output: string;
  durationMs: number;
  success: boolean;
};

export type ConsensusResult = {
  consensus: string;
  confidence: number;
  results: SwarmResult[];
};

export type ProviderLoad = {
  provider: string;
  activeTasks: number;
  totalCompleted: number;
};

type ProviderEntry = {
  name: string;
  priority: number;
};

const ROUTE_MAP: Record<SwarmTask['type'], string> = {
  code: 'claude',
  research: 'gemini',
  quick: 'qwen',
  review: 'claude',
};

export class CliSwarm {
  private providers: ProviderEntry[] = [];
  private load = new Map<string, ProviderLoad>();

  addProvider(name: string, priority: number): void {
    this.providers.push({ name, priority });
    this.load.set(name, { provider: name, activeTasks: 0, totalCompleted: 0 });
  }

  routeTask(task: SwarmTask): string {
    const preferred = ROUTE_MAP[task.type];
    const found = this.providers.find((p) => p.name === preferred);
    if (found) return found.name;

    // fallback: highest priority available
    const sorted = [...this.providers].sort((a, b) => b.priority - a.priority);
    const fallback = sorted[0];
    if (!fallback) throw new Error('No providers registered');
    return fallback.name;
  }

  async executeParallel(tasks: SwarmTask[]): Promise<SwarmResult[]> {
    return Promise.all(tasks.map((task) => this._executeOne(task)));
  }

  private async _executeOne(task: SwarmTask): Promise<SwarmResult> {
    const provider = this.routeTask(task);
    const entry = this.load.get(provider);
    if (entry) entry.activeTasks += 1;

    const start = Date.now();
    // Simulated execution — no external deps
    await Promise.resolve();
    const durationMs = Date.now() - start;

    if (entry) {
      entry.activeTasks -= 1;
      entry.totalCompleted += 1;
    }

    return {
      taskId: task.id,
      provider,
      output: `[${provider}] executed: ${task.prompt}`,
      durationMs,
      success: true,
    };
  }

  crossVerify(task: SwarmTask, providerResults: SwarmResult[]): ConsensusResult {
    const successful = providerResults.filter((r) => r.success);
    if (successful.length === 0) {
      return { consensus: '', confidence: 0, results: providerResults };
    }

    // Majority vote by output equality
    const tally = new Map<string, number>();
    for (const r of successful) {
      tally.set(r.output, (tally.get(r.output) ?? 0) + 1);
    }

    let bestOutput = '';
    let bestCount = 0;
    for (const [output, count] of tally) {
      if (count > bestCount) {
        bestCount = count;
        bestOutput = output;
      }
    }

    const confidence = bestCount / successful.length;
    void task; // task available for future enrichment
    return { consensus: bestOutput, confidence, results: providerResults };
  }

  getLoadBalance(): ProviderLoad[] {
    return [...this.load.values()];
  }
}
