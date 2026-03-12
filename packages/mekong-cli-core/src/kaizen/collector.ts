/**
 * Metrics Collector — gathers data from all modules into unified time series.
 * Storage: ~/.mekong/kaizen/metrics.jsonl (append-only, rotated monthly)
 */
import { promises as fs } from 'fs';
import { on } from '../core/events.js';
import type { MetricPoint, MetricSeries } from './types.js';

export class MetricsCollector {
  private buffer: MetricPoint[] = [];
  private readonly metricsPath: string;

  constructor(metricsDir: string) {
    this.metricsPath = `${metricsDir}/metrics.jsonl`;
  }

  /** Record a single metric point */
  record(name: string, value: number, unit: string, labels: Record<string, string> = {}): void {
    this.buffer.push({
      timestamp: new Date().toISOString(),
      value,
      labels: { metric: name, unit, ...labels },
    });
    if (this.buffer.length >= 100) void this.flush();
  }

  /** Convenience: record SOP step completion */
  recordSopStep(sopName: string, stepId: string, duration: number, success: boolean, cost: number): void {
    this.record('sop.step.duration', duration, 'ms', { sop: sopName, step: stepId });
    this.record('sop.step.success', success ? 1 : 0, 'count', { sop: sopName, step: stepId });
    this.record('sop.step.cost', cost, 'usd', { sop: sopName, step: stepId });
  }

  /** Convenience: record agent task completion */
  recordAgentTask(agent: string, duration: number, tokens: number, cost: number, success: boolean): void {
    this.record('agent.task.duration', duration, 'ms', { agent });
    this.record('agent.task.tokens', tokens, 'tokens', { agent });
    this.record('agent.task.cost', cost, 'usd', { agent });
    this.record('agent.task.success', success ? 1 : 0, 'count', { agent });
  }

  /** Convenience: record tool call */
  recordToolCall(tool: string, duration: number, success: boolean): void {
    this.record('tool.call.duration', duration, 'ms', { tool });
    this.record('tool.call.success', success ? 1 : 0, 'count', { tool });
  }

  /** Query metrics for a time range */
  async query(name: string, from: string, to: string, labels?: Record<string, string>): Promise<MetricSeries> {
    const fromMs = new Date(from).getTime();
    const toMs = new Date(to).getTime();

    let rawLines: string[] = [];
    try {
      const content = await fs.readFile(this.metricsPath, 'utf-8');
      rawLines = content.split('\n').filter(Boolean);
    } catch {
      // File doesn't exist yet — return empty series
    }

    // Also include in-memory buffer (not yet flushed)
    const bufferLines = this.buffer.map(p => JSON.stringify(p));
    const allLines = [...rawLines, ...bufferLines];

    const points: MetricPoint[] = [];
    for (const line of allLines) {
      try {
        const p = JSON.parse(line) as MetricPoint;
        const ts = new Date(p.timestamp).getTime();
        if (ts < fromMs || ts > toMs) continue;
        if (p.labels['metric'] !== name) continue;
        if (labels) {
          const matches = Object.entries(labels).every(([k, v]) => p.labels[k] === v);
          if (!matches) continue;
        }
        points.push(p);
      } catch {
        // skip malformed lines
      }
    }

    const unit = (points[0]?.labels['unit'] ?? 'count') as MetricSeries['unit'];
    return { name, unit, points };
  }

  /** Flush buffer to disk */
  async flush(): Promise<void> {
    if (this.buffer.length === 0) return;
    const dir = this.metricsPath.substring(0, this.metricsPath.lastIndexOf('/'));
    await fs.mkdir(dir, { recursive: true });
    const lines = this.buffer.map(p => JSON.stringify(p)).join('\n') + '\n';
    await fs.appendFile(this.metricsPath, lines, 'utf-8');
    this.buffer = [];
  }

  /** Rotate old metrics (keep last 90 days) */
  async rotate(): Promise<void> {
    let content: string;
    try {
      content = await fs.readFile(this.metricsPath, 'utf-8');
    } catch {
      return;
    }
    const cutoff = Date.now() - 90 * 24 * 60 * 60 * 1000;
    const kept = content
      .split('\n')
      .filter(Boolean)
      .filter(line => {
        try {
          const p = JSON.parse(line) as MetricPoint;
          return new Date(p.timestamp).getTime() >= cutoff;
        } catch {
          return false;
        }
      });
    await fs.writeFile(this.metricsPath, kept.join('\n') + (kept.length ? '\n' : ''), 'utf-8');
  }

  /** Subscribe to real-time events from event bus */
  subscribeToEvents(): void {
    on('sop:step_completed', (data) => {
      const d = data as { sopName?: string; stepId?: string; duration?: number; success?: boolean; cost?: number } | undefined;
      if (!d) return;
      this.recordSopStep(d.sopName ?? 'unknown', d.stepId ?? 'unknown', d.duration ?? 0, d.success ?? false, d.cost ?? 0);
    });

    on('agent:completed', (data) => {
      const d = data as { agent?: string; duration?: number; tokens?: number; cost?: number; success?: boolean } | undefined;
      if (!d) return;
      this.recordAgentTask(d.agent ?? 'unknown', d.duration ?? 0, d.tokens ?? 0, d.cost ?? 0, d.success ?? false);
    });

    on('tool:result', (data) => {
      const d = data as { tool?: string; duration?: number; success?: boolean } | undefined;
      if (!d) return;
      this.recordToolCall(d.tool ?? 'unknown', d.duration ?? 0, d.success ?? false);
    });

    on('budget:warning', (data) => {
      const d = data as { spent?: number } | undefined;
      this.record('budget.warning', d?.spent ?? 0, 'usd', {});
    });

    on('budget:exceeded', (data) => {
      const d = data as { spent?: number } | undefined;
      this.record('budget.exceeded', d?.spent ?? 0, 'usd', {});
    });
  }
}
