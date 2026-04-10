"use client";

// Collapsible group of tools by category

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { ToolCard } from "./tool-card";
import type { ToolDef, ToolCategory } from "@/lib/tool-types";

interface ToolCategoryGroupProps {
  category: ToolCategory;
  tools: ToolDef[];
  defaultOpen?: boolean;
}

const CATEGORY_LABELS: Record<ToolCategory, string> = {
  read:    "Read-Only",
  write:   "Write",
  execute: "Execute",
  meta:    "Meta",
  blocked: "Blocked",
};

const CATEGORY_COUNT_COLOR: Record<ToolCategory, string> = {
  read:    "var(--status-info)",
  write:   "var(--model-reasoning)",
  execute: "var(--accent-teal-400)",
  meta:    "var(--model-audit)",
  blocked: "var(--status-danger)",
};

export function ToolCategoryGroup({ category, tools, defaultOpen = true }: ToolCategoryGroupProps) {
  const [open, setOpen] = useState(defaultOpen);

  if (tools.length === 0) return null;

  return (
    <div>
      {/* Group header */}
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          gap: "0.375rem",
          padding: "0.25rem 0.5rem",
          background: "var(--bg-primary)",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        {open ? (
          <ChevronDown size={11} style={{ color: "var(--text-muted)" }} />
        ) : (
          <ChevronRight size={11} style={{ color: "var(--text-muted)" }} />
        )}
        <span
          style={{
            fontSize: "0.65rem",
            fontWeight: 600,
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          {CATEGORY_LABELS[category]}
        </span>
        <span
          style={{
            fontSize: "0.6rem",
            padding: "0 4px",
            borderRadius: "9999px",
            background: `${CATEGORY_COUNT_COLOR[category]}22`,
            color: CATEGORY_COUNT_COLOR[category],
            marginLeft: "auto",
          }}
        >
          {tools.length}
        </span>
      </button>

      {/* Tool list */}
      {open && (
        <div style={{ padding: "0.125rem 0.25rem 0.375rem" }}>
          {tools.map((tool) => (
            <ToolCard key={tool.id} tool={tool} />
          ))}
        </div>
      )}
    </div>
  );
}
