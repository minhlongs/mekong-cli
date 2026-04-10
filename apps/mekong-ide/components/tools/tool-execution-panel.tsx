"use client";

// Tool Execution Panel — 5 category groups + live call log

import { useState, useMemo } from "react";
import { Search } from "lucide-react";
import { ToolCategoryGroup } from "./tool-category-group";
import { ToolCallLog } from "./tool-call-log";
import { MOCK_TOOLS, MOCK_TOOL_CALLS } from "@/lib/mock/tool-mock-data";
import type { ToolCategory } from "@/lib/tool-types";

const CATEGORY_ORDER: ToolCategory[] = ["read", "write", "execute", "meta", "blocked"];

export function ToolExecutionPanel() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return MOCK_TOOLS;
    const q = query.toLowerCase();
    return MOCK_TOOLS.filter(
      (t) => t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q)
    );
  }, [query]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header with search */}
      <div
        style={{
          padding: "0.5rem 0.625rem",
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-secondary)",
          display: "flex",
          gap: "0.375rem",
          alignItems: "center",
        }}
      >
        <Search size={13} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search tools..."
          style={{
            flex: 1,
            fontSize: "0.72rem",
            background: "transparent",
            border: "none",
            color: "var(--text-primary)",
            outline: "none",
            fontFamily: "inherit",
          }}
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            style={{
              fontSize: "0.65rem",
              color: "var(--text-muted)",
              background: "none",
              border: "none",
              cursor: "pointer",
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Scrollable tool list */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {CATEGORY_ORDER.map((cat) => {
          const tools = filtered.filter((t) => t.category === cat);
          return (
            <ToolCategoryGroup
              key={cat}
              category={cat}
              tools={tools}
              defaultOpen={cat !== "blocked"}
            />
          );
        })}
      </div>

      {/* Live call log — fixed at bottom */}
      <div
        style={{
          borderTop: "1px solid var(--border-subtle)",
          maxHeight: "9rem",
          overflowY: "auto",
          background: "var(--bg-secondary)",
        }}
      >
        <ToolCallLog calls={MOCK_TOOL_CALLS} />
      </div>
    </div>
  );
}
