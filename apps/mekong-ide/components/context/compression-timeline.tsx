"use client";
/**
 * CompressionTimeline — horizontal track with dots at compression events.
 * Hover tooltip shows before/after token counts.
 */
import { useState } from "react";
import type { CompressionEvent } from "@/lib/types/context-types";

interface CompressionTimelineProps {
  events: CompressionEvent[];
  sessionDurationSec: number;
}

const typeColor: Record<CompressionEvent["type"], string> = {
  compact: "var(--accent-teal-500)",
  prune:   "var(--status-warning)",
  reset:   "var(--status-danger)",
};

const typeLabel: Record<CompressionEvent["type"], string> = {
  compact: "C",
  prune:   "P",
  reset:   "R",
};

export function CompressionTimeline({ events, sessionDurationSec }: CompressionTimelineProps) {
  const [tooltip, setTooltip] = useState<string | null>(null);

  return (
    <div>
      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.5rem", display: "flex", gap: "0.75rem" }}>
        <span style={{ color: "var(--text-secondary)", fontWeight: 500 }}>Compression Timeline</span>
        {(["compact", "prune", "reset"] as const).map((t) => (
          <span key={t} style={{ display: "flex", alignItems: "center", gap: "0.2rem" }}>
            <span style={{ color: typeColor[t], fontWeight: 700 }}>{typeLabel[t]}</span>
            <span style={{ color: "var(--text-muted)" }}>{t}</span>
          </span>
        ))}
      </div>

      <div style={{ position: "relative", height: "2rem" }}>
        {/* Track line */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: 0,
            right: 0,
            height: "1px",
            background: "var(--border-strong)",
            transform: "translateY(-50%)",
          }}
        />
        {/* "now" label */}
        <div style={{ position: "absolute", right: 0, top: "50%", transform: "translateY(-150%)", fontSize: "0.6rem", color: "var(--text-muted)" }}>
          now
        </div>

        {/* Event dots */}
        {events.map((ev) => {
          const leftPct = (ev.offsetSec / sessionDurationSec) * 100;
          const color = typeColor[ev.type];
          return (
            <div
              key={ev.id}
              style={{
                position: "absolute",
                left: `${leftPct}%`,
                top: "50%",
                transform: "translate(-50%, -50%)",
                cursor: "pointer",
                zIndex: 2,
              }}
              onMouseEnter={() =>
                setTooltip(
                  `${ev.id} — ${ev.type}\n${(ev.tokensBefore / 1000).toFixed(1)}K → ${(ev.tokensAfter / 1000).toFixed(1)}K (${Math.round(ev.ratio * 100)}%)`
                )
              }
              onMouseLeave={() => setTooltip(null)}
            >
              <div
                style={{
                  width: "0.75rem",
                  height: "0.75rem",
                  borderRadius: "50%",
                  background: color,
                  border: "2px solid var(--bg-primary)",
                  boxShadow: `0 0 0 1px ${color}`,
                }}
              />
              <span style={{ position: "absolute", top: "0.9rem", left: "50%", transform: "translateX(-50%)", fontSize: "0.6rem", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                {ev.id}
              </span>
            </div>
          );
        })}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          style={{
            marginTop: "0.5rem",
            fontSize: "0.7rem",
            color: "var(--text-secondary)",
            background: "var(--surface-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.25rem",
            padding: "0.375rem 0.5rem",
            whiteSpace: "pre",
          }}
        >
          {tooltip}
        </div>
      )}
    </div>
  );
}
