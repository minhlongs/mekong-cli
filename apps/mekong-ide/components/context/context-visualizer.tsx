"use client";
/**
 * ContextVisualizer — 340px embeddable strip.
 * Composes: TokenUsageBar, CompressionTimeline, ContextMetricsRow.
 */
import { TokenUsageBar } from "./token-usage-bar";
import { CompressionTimeline } from "./compression-timeline";
import { ContextMetricsRow } from "./context-metrics-row";
import { useContextMetrics } from "@/hooks/use-context-metrics";
import { MOCK_CONTEXT } from "@/lib/mock/context-mock-data";

export function ContextVisualizer() {
  const { metrics, isDemoMode } = useContextMetrics();

  // Fallback to mock while loading or in demo mode
  const data = metrics ?? MOCK_CONTEXT;
  const { tokenUsage, compressionEvents, sessionDurationSec, estimatedCostUsd } = data;
  const usedTokens =
    tokenUsage.systemPrompt +
    tokenUsage.claudeMd +
    tokenUsage.conversation +
    tokenUsage.toolResults;

  return (
    <div
      style={{
        minHeight: "340px",
        background: "var(--bg-secondary)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
        padding: "1rem 1.25rem",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
          Context Usage
          {isDemoMode && (
            <span style={{ marginLeft: "0.5rem", fontSize: "0.65rem", color: "var(--text-muted)" }}>
              (demo)
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
            {(usedTokens / 1000).toFixed(1)}K / {(tokenUsage.total / 1000).toFixed(0)}K tokens
          </span>
          <span style={{ fontSize: "0.75rem", color: "var(--status-success)" }}>
            ${estimatedCostUsd.toFixed(4)}
          </span>
        </div>
      </div>

      {/* Token bar */}
      <div style={{ paddingTop: "0.75rem" }}>
        <TokenUsageBar usage={tokenUsage} />
      </div>

      {/* Compression timeline */}
      <CompressionTimeline
        events={compressionEvents}
        sessionDurationSec={sessionDurationSec}
      />

      {/* Metrics row */}
      <ContextMetricsRow metrics={data} />
    </div>
  );
}
