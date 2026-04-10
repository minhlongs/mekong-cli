"use client";

import { useState } from "react";
import { X, Plus, Terminal, AlertCircle, FileText } from "lucide-react";
import clsx from "clsx";

interface TerminalPanelProps {
  /** Whether the terminal panel is visible */
  visible?: boolean;
  onClose?: () => void;
}

type TerminalTab = "terminal" | "output" | "problems";

const TERMINAL_CONTENT = `OpenClaw IDE v1.0.0 — Mekong Engine
$ pnpm dev
  ▲ Next.js 15.3.0
  - Local: http://localhost:3000
  ✓ Starting...
  ✓ Ready in 842ms`;

/**
 * Bottom terminal panel with tabs: Terminal, Output, Problems.
 * Fixed 200px height. Monospace dark surface.
 */
export function TerminalPanel({ visible = true, onClose }: TerminalPanelProps) {
  const [activeTab, setActiveTab] = useState<TerminalTab>("terminal");

  if (!visible) return null;

  const TABS: { id: TerminalTab; label: string; icon: React.ElementType }[] = [
    { id: "terminal", label: "Terminal", icon: Terminal },
    { id: "output", label: "Output", icon: FileText },
    { id: "problems", label: "Problems", icon: AlertCircle },
  ];

  return (
    <div
      className="flex flex-col shrink-0"
      style={{
        height: "200px",
        backgroundColor: "var(--bg-secondary)",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      {/* Tab bar */}
      <div
        className="flex items-center justify-between px-2 h-8 shrink-0"
        style={{ borderBottom: "1px solid var(--border-subtle)" }}
      >
        <div className="flex items-center">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={clsx(
                "flex items-center gap-1.5 px-3 h-8 text-xs transition-colors",
                activeTab === id
                  ? "text-[var(--text-primary)] border-b border-[var(--accent-teal-400)]"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
              )}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={12} />
              {label}
            </button>
          ))}
          <button
            className="px-2 h-8 text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
            aria-label="New terminal"
          >
            <Plus size={12} />
          </button>
        </div>

        <button
          onClick={onClose}
          className="p-1 text-[var(--text-muted)] hover:text-[var(--text-secondary)] rounded hover:bg-[var(--surface-hover)]"
          aria-label="Close terminal"
        >
          <X size={14} />
        </button>
      </div>

      {/* Terminal content */}
      <div className="flex-1 overflow-y-auto p-3">
        {activeTab === "terminal" && (
          <pre
            className="text-xs leading-relaxed whitespace-pre-wrap"
            style={{
              fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
              color: "var(--status-success)",
            }}
          >
            {TERMINAL_CONTENT}
            <span className="animate-pulse">█</span>
          </pre>
        )}
        {activeTab === "output" && (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No output.
          </p>
        )}
        {activeTab === "problems" && (
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            No problems detected.
          </p>
        )}
      </div>
    </div>
  );
}
