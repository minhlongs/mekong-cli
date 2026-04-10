// Single tool call log entry: tool name, status, duration

import { CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import type { ToolCall } from "@/lib/tool-types";

interface ToolCallEntryProps {
  call: ToolCall;
}

const STATUS_ICON = {
  running:  <Loader2 size={12} className="animate-spin" style={{ color: "var(--accent-teal-400)" }} />,
  complete: <CheckCircle2 size={12} style={{ color: "var(--status-success)" }} />,
  error:    <AlertCircle size={12} style={{ color: "var(--status-danger)" }} />,
};

export function ToolCallEntry({ call }: ToolCallEntryProps) {
  const relSec = Math.round((Date.now() - call.timestamp) / 1000);
  const timeAgo = relSec < 60 ? `${relSec}s ago` : `${Math.round(relSec / 60)}m ago`;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "0.375rem",
        padding: "0.3rem 0.5rem",
        borderRadius: "0.25rem",
        background: "var(--bg-primary)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      {/* Status icon */}
      <span style={{ marginTop: "1px", flexShrink: 0 }}>
        {STATUS_ICON[call.status]}
      </span>

      {/* Tool name + args + result */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: "0.7rem", fontWeight: 500, color: "var(--text-primary)", fontFamily: "monospace" }}>
          {call.toolName}
          <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>
            ({Object.values(call.args).join(", ")})
          </span>
        </div>
        {call.result && (
          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginTop: "1px" }}>
            {call.result}
          </div>
        )}
      </div>

      {/* Timing */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "1px", flexShrink: 0 }}>
        {call.durationMs !== undefined && (
          <span style={{ fontSize: "0.65rem", color: "var(--accent-teal-400)" }}>
            {call.durationMs}ms
          </span>
        )}
        <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>{timeAgo}</span>
      </div>
    </div>
  );
}
