"use client";

/**
 * SignalEntry — single LLM signal row: model badge, direction, ticker, confidence, timestamp.
 */

import { Badge } from "@/components/ds";
import type { LlmSignal, SignalDirection } from "@/lib/types/trading-types";
import type { BadgeVariant } from "@/lib/types";

interface SignalEntryProps {
  signal: LlmSignal;
}

const directionVariant: Record<SignalDirection, BadgeVariant> = {
  buy: "success",
  sell: "danger",
  hold: "warning",
};

export function SignalEntry({ signal }: SignalEntryProps) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "0.5rem",
      padding: "0.5rem 0.75rem",
      borderBottom: "1px solid var(--border-subtle)",
      fontSize: "0.8125rem",
    }}>
      {/* Model dot + name */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.25rem", minWidth: 80 }}>
        <span style={{
          width: "0.5rem", height: "0.5rem", borderRadius: "50%", flexShrink: 0,
          background: `var(--model-${signal.modelVariant})`,
        }} />
        <span style={{ color: `var(--model-${signal.modelVariant})`, fontSize: "0.75rem", fontWeight: 500 }}>
          {signal.model}
        </span>
      </div>

      {/* Direction badge */}
      <Badge variant={directionVariant[signal.direction]} label={signal.direction.toUpperCase()} />

      {/* Ticker */}
      <span style={{ fontWeight: 600, color: "var(--text-primary)", minWidth: 48 }}>
        {signal.ticker}
      </span>

      {/* Confidence */}
      <span style={{
        fontSize: "0.75rem",
        color: signal.confidence >= 80 ? "var(--status-success)" : signal.confidence >= 60 ? "var(--status-warning)" : "var(--text-muted)",
      }}>
        {signal.confidence}%
      </span>

      {/* Reasoning (truncated) */}
      <span style={{ flex: 1, color: "var(--text-muted)", fontSize: "0.75rem", overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>
        {signal.reasoning}
      </span>

      {/* Timestamp */}
      <span style={{ color: "var(--text-muted)", fontSize: "0.75rem", flexShrink: 0 }}>
        {signal.timestamp}
      </span>
    </div>
  );
}
