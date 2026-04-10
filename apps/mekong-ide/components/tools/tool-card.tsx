// Single tool item: icon, name, description, hotkey badge, approval indicator

import { FileSearch, FilePen, Terminal, Settings, ShieldOff } from "lucide-react";
import type { ToolDef } from "@/lib/tool-types";

interface ToolCardProps {
  tool: ToolDef;
}

const CATEGORY_ICON = {
  read:    <FileSearch size={13} />,
  write:   <FilePen size={13} />,
  execute: <Terminal size={13} />,
  meta:    <Settings size={13} />,
  blocked: <ShieldOff size={13} />,
};

const CATEGORY_ACCENT: Record<string, string> = {
  read:    "var(--status-info)",
  write:   "var(--model-reasoning)",
  execute: "var(--accent-teal-400)",
  meta:    "var(--model-audit)",
  blocked: "var(--status-danger)",
};

export function ToolCard({ tool }: ToolCardProps) {
  const isBlocked = tool.category === "blocked";
  const accentColor = CATEGORY_ACCENT[tool.category];

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "0.5rem",
        padding: "0.375rem 0.5rem",
        borderRadius: "0.25rem",
        background: isBlocked ? "rgba(239,68,68,0.04)" : "transparent",
        border: isBlocked ? "1px solid rgba(239,68,68,0.12)" : "1px solid transparent",
        opacity: isBlocked ? 0.7 : 1,
      }}
    >
      {/* Icon */}
      <span style={{ color: accentColor, marginTop: "2px", flexShrink: 0 }}>
        {CATEGORY_ICON[tool.category]}
      </span>

      {/* Name + description */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
          <span
            style={{
              fontSize: "0.72rem",
              fontWeight: 500,
              color: isBlocked ? "var(--status-danger)" : "var(--text-primary)",
              fontFamily: "monospace",
            }}
          >
            {tool.name}
          </span>
          {tool.approvalRequired && !isBlocked && (
            <span
              style={{
                fontSize: "0.6rem",
                padding: "1px 4px",
                borderRadius: "3px",
                background: "rgba(234,179,8,0.15)",
                color: "var(--status-warning)",
              }}
            >
              approval
            </span>
          )}
        </div>
        <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginTop: "1px" }}>
          {tool.description}
        </div>
      </div>

      {/* Hotkey badge */}
      {tool.hotkey && (
        <span
          style={{
            fontSize: "0.6rem",
            padding: "1px 5px",
            borderRadius: "3px",
            background: "var(--surface-active)",
            color: "var(--text-muted)",
            fontFamily: "monospace",
            flexShrink: 0,
          }}
        >
          {tool.hotkey}
        </span>
      )}
    </div>
  );
}
