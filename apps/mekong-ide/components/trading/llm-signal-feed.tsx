"use client";

/**
 * LlmSignalFeed — scrollable list of LLM trading signals, auto-scrolls to bottom on new entries.
 */

import { useEffect, useRef } from "react";
import { SignalEntry } from "./signal-entry";
import type { LlmSignal } from "@/lib/types/trading-types";

interface LlmSignalFeedProps {
  signals: LlmSignal[];
}

export function LlmSignalFeed({ signals }: LlmSignalFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [signals.length]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Feed header */}
      <div style={{
        padding: "0.5rem 0.75rem",
        borderBottom: "1px solid var(--border-subtle)",
        fontSize: "0.75rem",
        fontWeight: 600,
        color: "var(--text-muted)",
        textTransform: "uppercase",
        letterSpacing: "0.05em",
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        flexShrink: 0,
        background: "var(--surface-card)",
      }}>
        <span style={{ width: "0.5rem", height: "0.5rem", borderRadius: "50%", background: "var(--status-success)", animation: "pulse 1.5s ease-in-out infinite" }} />
        LLM Signal Feed
        <span style={{ marginLeft: "auto", color: "var(--text-muted)" }}>{signals.length} signals</span>
      </div>

      {/* Scrollable list */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {signals.map((signal) => (
          <SignalEntry key={signal.id} signal={signal} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
