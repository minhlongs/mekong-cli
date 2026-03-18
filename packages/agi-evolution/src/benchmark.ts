export type BenchmarkTool = 'openclaw' | 'cursor' | 'windsurf' | 'cline' | 'aider';

export interface BenchmarkResult {
  tool: BenchmarkTool;
  task: string;
  durationMs: number;
  accuracy: number;
  costUsd: number;
  timestamp: Date;
}

export interface ToolSummary {
  tool: BenchmarkTool;
  runs: number;
  avgDurationMs: number;
  avgAccuracy: number;
  avgCostUsd: number;
  totalCostUsd: number;
}

export interface ComparisonReport {
  tools: ToolSummary[];
  fastest: BenchmarkTool;
  mostAccurate: BenchmarkTool;
  cheapest: BenchmarkTool;
  generatedAt: Date;
}

export class BenchmarkRunner {
  private readonly results: BenchmarkResult[] = [];

  recordBenchmark(tool: BenchmarkTool, task: string, metrics: Omit<BenchmarkResult, 'tool' | 'task' | 'timestamp'>): void {
    this.results.push({ tool, task, ...metrics, timestamp: new Date() });
  }

  compareTools(tools: BenchmarkTool[]): ComparisonReport {
    const summaries: ToolSummary[] = tools.map((tool) => {
      const runs = this.results.filter((r) => r.tool === tool);
      if (runs.length === 0) {
        return { tool, runs: 0, avgDurationMs: 0, avgAccuracy: 0, avgCostUsd: 0, totalCostUsd: 0 };
      }
      const avgDurationMs = runs.reduce((s, r) => s + r.durationMs, 0) / runs.length;
      const avgAccuracy = runs.reduce((s, r) => s + r.accuracy, 0) / runs.length;
      const totalCostUsd = runs.reduce((s, r) => s + r.costUsd, 0);
      return { tool, runs: runs.length, avgDurationMs, avgAccuracy, avgCostUsd: totalCostUsd / runs.length, totalCostUsd };
    });

    const ranked = summaries.filter((s) => s.runs > 0);
    const fastest = ranked.length ? ranked.reduce((a, b) => (a.avgDurationMs < b.avgDurationMs ? a : b)).tool : tools[0];
    const mostAccurate = ranked.length ? ranked.reduce((a, b) => (a.avgAccuracy > b.avgAccuracy ? a : b)).tool : tools[0];
    const cheapest = ranked.length ? ranked.reduce((a, b) => (a.avgCostUsd < b.avgCostUsd ? a : b)).tool : tools[0];

    return { tools: summaries, fastest, mostAccurate, cheapest, generatedAt: new Date() };
  }

  generateCompetitiveReport(): string {
    const allTools: BenchmarkTool[] = ['openclaw', 'cursor', 'windsurf', 'cline', 'aider'];
    const report = this.compareTools(allTools);
    const lines: string[] = [
      '# OpenClaw Competitive Benchmark Report',
      `> Generated: ${report.generatedAt.toISOString()}`,
      '',
      '## Summary',
      `- **Fastest**: ${report.fastest}`,
      `- **Most Accurate**: ${report.mostAccurate}`,
      `- **Cheapest**: ${report.cheapest}`,
      '',
      '## Tool Comparison',
      '| Tool | Runs | Avg Duration (ms) | Avg Accuracy | Avg Cost ($) |',
      '|------|------|-------------------|--------------|--------------|',
    ];

    for (const s of report.tools) {
      lines.push(
        `| ${s.tool} | ${s.runs} | ${s.avgDurationMs.toFixed(0)} | ${(s.avgAccuracy * 100).toFixed(1)}% | $${s.avgCostUsd.toFixed(4)} |`,
      );
    }

    lines.push('', `_Total benchmark runs: ${this.results.length}_`);
    return lines.join('\n');
  }

  getResults(): BenchmarkResult[] {
    return [...this.results];
  }
}
