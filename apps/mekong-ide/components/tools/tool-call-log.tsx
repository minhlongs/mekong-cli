// Live tool call log — scrollable feed of recent invocations

import { Activity } from "lucide-react";
import { ToolCallEntry } from "./tool-call-entry";
import type { ToolCall } from "@/lib/tool-types";

interface ToolCallLogProps {
  calls: ToolCall[];
}

export function ToolCallLog({ calls }: ToolCallLogProps) {
  return (
    <div>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.375rem",
          padding: "0.375rem 0.5rem",
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-primary)",
        }}
      >
        <Activity size={12} style={{ color: "var(--accent-teal-400)" }} />
        <span
          style={{
            fontSize: "0.65rem",
            fontWeight: 600,
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          Live Call Log
        </span>
        {calls.some((c) => c.status === "running") && (
          <span
            style={{
              width: "0.4rem",
              height: "0.4rem",
              borderRadius: "50%",
              background: "var(--accent-teal-400)",
              marginLeft: "auto",
              animation: "pulse 1s infinite",
            }}
          />
        )}
      </div>

      {/* Entries */}
      <div style={{ padding: "0.25rem 0.375rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
        {calls.length === 0 ? (
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", padding: "0.5rem", textAlign: "center" }}>
            No tool calls yet
          </div>
        ) : (
          calls.map((call) => <ToolCallEntry key={call.id} call={call} />)
        )}
      </div>
    </div>
  );
}
