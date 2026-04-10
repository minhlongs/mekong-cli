"use client";
/**
 * ContextMetricsRow — 4 stat cards: Tokens Used, Cache Hits, Avg Latency, Session Cost.
 */
import type { ContextMetrics } from "@/lib/types/context-types";

interface ContextMetricsRowProps {
  metrics: ContextMetrics;
}

interface MetricCellProps {
  label: string;
  value: string;
  sub?: string;
  color?: string;
}

function MetricCell({ label, value, sub, color = "var(--text-primary)" }: MetricCellProps) {
  return (
    <div
      style={{
        flex: 1,
        padding: "0.75rem 1rem",
        borderRight: "1px solid var(--border-subtle)",
        display: "flex",
        flexDirection: "column",
        gap: "0.2rem",
      }}
    >
      <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>{label}</div>
      <div style={{ fontSize: "1.25rem", fontWeight: 700, color }}>{value}</div>
      {sub && <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{sub}</div>}
    </div>
  );
}

export function ContextMetricsRow({ metrics }: ContextMetricsRowProps) {
  const { tokenUsage, cacheHits, avgLatencyMs, estimatedCostUsd } = metrics;
  const usedTokens = tokenUsage.systemPrompt + tokenUsage.claudeMd + tokenUsage.conversation + tokenUsage.toolResults;
  const comprRatio  = metrics.compressionEvents.length > 0
    ? Math.round((1 - metrics.compressionEvents.at(-1)!.ratio) * 100)
    : 0;

  return (
    <div
      style={{
        display: "flex",
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        overflow: "hidden",
      }}
    >
      <MetricCell
        label="Tokens Used"
        value={`${(usedTokens / 1000).toFixed(1)}K`}
        sub={`of ${(tokenUsage.total / 1000).toFixed(0)}K total`}
        color="var(--accent-teal-400)"
      />
      <MetricCell
        label="Cache Hits"
        value={String(cacheHits)}
        sub="this session"
        color="var(--model-audit)"
      />
      <MetricCell
        label="Avg Latency"
        value={`${avgLatencyMs}ms`}
        sub="tool calls"
        color="var(--text-secondary)"
      />
      {/* Last cell — no right border */}
      <div style={{ flex: 1, padding: "0.75rem 1rem", display: "flex", flexDirection: "column", gap: "0.2rem" }}>
        <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Session Cost</div>
        <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--status-success)" }}>${estimatedCostUsd.toFixed(2)}</div>
        {comprRatio > 0 && <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{comprRatio}% saved by compression</div>}
      </div>
    </div>
  );
}
