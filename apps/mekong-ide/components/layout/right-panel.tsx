"use client";

// Right panel with [Chat] / [Tools] tab switcher

import { useState } from "react";
import { Bot, Wrench } from "lucide-react";
import { AgentChatPanel } from "@/components/agent";
import { ToolExecutionPanel } from "@/components/tools";

type Tab = "chat" | "tools";

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "chat", label: "Chat", icon: <Bot size={13} /> },
  { id: "tools", label: "Tools", icon: <Wrench size={13} /> },
];

/**
 * Right agent panel — Phase 3 adds Chat/Tools tab switcher.
 * Width is controlled by IdeShell (resizable, default 320px).
 */
export function RightPanel() {
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "var(--bg-secondary)",
        borderLeft: "1px solid var(--border-subtle)",
      }}
    >
      {/* Tab bar */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-primary)",
          flexShrink: 0,
        }}
      >
        {TABS.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "0.3rem",
                padding: "0.5rem",
                background: "none",
                border: "none",
                borderBottom: isActive
                  ? "2px solid var(--accent-teal-500)"
                  : "2px solid transparent",
                color: isActive ? "var(--accent-teal-400)" : "var(--text-muted)",
                fontSize: "0.72rem",
                fontWeight: isActive ? 600 : 400,
                cursor: "pointer",
                transition: "color 0.15s",
              }}
            >
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Panel content */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
        {activeTab === "chat" ? <AgentChatPanel /> : <ToolExecutionPanel />}
      </div>
    </div>
  );
}
