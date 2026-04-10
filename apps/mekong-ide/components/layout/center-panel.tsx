"use client";

import { useState } from "react";
import { TabBar, type TabItem } from "./tab-bar";
import { TerminalPanel } from "./terminal-panel";

interface CenterPanelProps {
  /** Whether terminal panel is visible */
  terminalVisible?: boolean;
  onTerminalToggle?: () => void;
  children?: React.ReactNode;
}

const DEFAULT_TABS: TabItem[] = [
  { id: "welcome", label: "Welcome", ext: "md" },
  { id: "ide-shell", label: "ide-shell.tsx", ext: "tsx", modified: false },
  { id: "readme", label: "README.md", ext: "md" },
];

const PLACEHOLDER_CODE = `// ide-shell.tsx — Mekong IDE Core Shell
// Three-panel layout orchestrator

import { LeftSidebar } from "@/components/layout/left-sidebar";
import { CenterPanel } from "@/components/layout/center-panel";
import { RightPanel } from "@/components/layout/right-panel";

interface IdeShellProps {
  showRightPanel?: boolean;
}

export function IdeShell({ showRightPanel = true }: IdeShellProps) {
  return (
    <div className="grid h-screen" style={{
      gridTemplateColumns: \`48px 1fr \${showRightPanel ? "320px" : "0"}\`,
    }}>
      <LeftSidebar />
      <CenterPanel />
      {showRightPanel && <RightPanel />}
    </div>
  );
}`;

/**
 * Center panel: tab bar + editor area + terminal.
 * Flex column layout taking all available horizontal space.
 */
export function CenterPanel({
  terminalVisible = true,
  onTerminalToggle,
  children,
}: CenterPanelProps) {
  const [tabs, setTabs] = useState<TabItem[]>(DEFAULT_TABS);
  const [activeTabId, setActiveTabId] = useState("ide-shell");

  function handleTabClose(id: string) {
    setTabs((prev) => {
      const next = prev.filter((t) => t.id !== id);
      if (activeTabId === id && next.length > 0) {
        setActiveTabId(next[next.length - 1].id);
      }
      return next;
    });
  }

  function handleTabAdd() {
    const id = `untitled-${Date.now()}`;
    setTabs((prev) => [...prev, { id, label: `Untitled`, modified: true }]);
    setActiveTabId(id);
  }

  return (
    <div
      className="flex flex-col h-full overflow-hidden"
      style={{ backgroundColor: "var(--bg-primary)" }}
    >
      <TabBar
        tabs={tabs}
        activeTabId={activeTabId}
        onTabSelect={setActiveTabId}
        onTabClose={handleTabClose}
        onTabAdd={handleTabAdd}
      />

      {/* Editor area */}
      <div className="flex-1 overflow-hidden flex">
        {children ?? (
          <div className="flex-1 overflow-auto">
            {/* Line numbers + code */}
            <div className="flex min-h-full">
              {/* Gutter */}
              <div
                className="select-none text-right pr-4 pt-4 text-xs leading-6 min-w-[48px]"
                style={{
                  color: "var(--text-muted)",
                  backgroundColor: "var(--bg-primary)",
                  fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                  borderRight: "1px solid var(--border-subtle)",
                }}
              >
                {PLACEHOLDER_CODE.split("\n").map((_, i) => (
                  <div key={i}>{i + 1}</div>
                ))}
              </div>
              {/* Code */}
              <pre
                className="flex-1 p-4 text-xs leading-6 overflow-x-auto"
                style={{
                  fontFamily: "var(--font-mono, 'JetBrains Mono', monospace)",
                  color: "var(--text-primary)",
                }}
              >
                {PLACEHOLDER_CODE}
              </pre>
            </div>
          </div>
        )}
      </div>

      <TerminalPanel
        visible={terminalVisible}
        onClose={onTerminalToggle}
      />
    </div>
  );
}
