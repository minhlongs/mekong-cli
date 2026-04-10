"use client";
/**
 * TokenUsageBar — stacked horizontal bar with 4 segments + 75%/90% threshold markers.
 */
import type { TokenUsage } from "@/lib/types/context-types";

interface TokenUsageBarProps {
  usage: TokenUsage;
}

const SEGMENTS = [
  { key: "systemPrompt" as const, label: "System",       color: "var(--model-audit)"      },
  { key: "claudeMd"     as const, label: "CLAUDE.md",    color: "var(--model-architect)"  },
  { key: "conversation" as const, label: "Conversation", color: "var(--accent-teal-500)"  },
  { key: "toolResults"  as const, label: "Tools",        color: "var(--model-reasoning)"  },
];

export function TokenUsageBar({ usage }: TokenUsageBarProps) {
  const usedTokens = usage.systemPrompt + usage.claudeMd + usage.conversation + usage.toolResults;
  const usedPct    = Math.round((usedTokens / usage.total) * 100);

  return (
    <div>
      {/* Label row */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {SEGMENTS.map((seg) => (
            <div key={seg.key} style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <div style={{ width: "0.5rem", height: "0.5rem", borderRadius: "2px", background: seg.color }} />
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{seg.label}</span>
            </div>
          ))}
          <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
            <div style={{ width: "0.5rem", height: "0.5rem", borderRadius: "2px", background: "var(--border-strong)" }} />
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>Available</span>
          </div>
        </div>
        <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", fontWeight: 600 }}>
          {(usedTokens / 1000).toFixed(1)}K / {(usage.total / 1000).toFixed(0)}K ({usedPct}%)
        </span>
      </div>

      {/* Stacked bar with markers */}
      <div style={{ position: "relative", height: "1rem", background: "var(--border-subtle)", borderRadius: "0.25rem", overflow: "visible" }}>
        {/* Segments */}
        <div style={{ display: "flex", height: "100%", borderRadius: "0.25rem", overflow: "hidden" }}>
          {SEGMENTS.map((seg) => {
            const pct = (usage[seg.key] / usage.total) * 100;
            return (
              <div
                key={seg.key}
                title={`${seg.label}: ${(usage[seg.key] / 1000).toFixed(1)}K`}
                style={{ height: "100%", width: `${pct}%`, background: seg.color, flexShrink: 0 }}
              />
            );
          })}
        </div>
        {/* 75% marker */}
        <Marker pct={75} label="75%" />
        {/* 90% marker */}
        <Marker pct={90} label="90%" />
      </div>
    </div>
  );
}

function Marker({ pct, label }: { pct: number; label: string }) {
  return (
    <div
      style={{
        position: "absolute",
        top: "-0.25rem",
        bottom: "-0.25rem",
        left: `${pct}%`,
        borderLeft: "1px dashed var(--text-muted)",
        zIndex: 1,
      }}
    >
      <span
        style={{
          position: "absolute",
          top: "-1.1rem",
          left: "0.2rem",
          fontSize: "0.6rem",
          color: "var(--text-muted)",
          whiteSpace: "nowrap",
        }}
      >
        {label}
      </span>
    </div>
  );
}
