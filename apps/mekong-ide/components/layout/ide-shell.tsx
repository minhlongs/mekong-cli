"use client";

import { useState, useEffect, useCallback } from "react";
import { LeftSidebar } from "./left-sidebar";
import { CenterPanel } from "./center-panel";
import { RightPanel } from "./right-panel";
import { PanelResizer } from "./panel-resizer";

interface IdeShellProps {
  children?: React.ReactNode;
}

/**
 * Root three-panel IDE layout.
 * Grid: 48px sidebar | flex-1 center | right panel (resizable, 320px default).
 *
 * Keyboard shortcuts:
 *   Ctrl+`       — toggle terminal
 *   Ctrl+B       — toggle sidebar (expand/collapse)
 *   Ctrl+Shift+B — toggle right panel
 */
export function IdeShell({ children }: IdeShellProps) {
  const [activeSection, setActiveSection] = useState("explorer");
  const [rightPanelWidth, setRightPanelWidth] = useState(320);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [showTerminal, setShowTerminal] = useState(true);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Ctrl+` — toggle terminal
      if (e.ctrlKey && e.key === "`") {
        e.preventDefault();
        setShowTerminal((v) => !v);
        return;
      }
      // Ctrl+Shift+B — toggle right panel
      if (e.ctrlKey && e.shiftKey && e.key === "B") {
        e.preventDefault();
        setShowRightPanel((v) => !v);
        return;
      }
      // Ctrl+B — reserved for sidebar expand (future: file tree panel)
      if (e.ctrlKey && !e.shiftKey && e.key === "b") {
        e.preventDefault();
        // Phase 3 will implement sidebar expansion; placeholder only
      }
    },
    []
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ backgroundColor: "var(--bg-primary)" }}
    >
      {/* Left sidebar: fixed 48px */}
      <LeftSidebar
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* Center panel: flex-1 */}
      <div className="flex-1 min-w-0 overflow-hidden">
        <CenterPanel
          terminalVisible={showTerminal}
          onTerminalToggle={() => setShowTerminal((v) => !v)}
        >
          {children}
        </CenterPanel>
      </div>

      {/* Resizer + Right panel */}
      {showRightPanel && (
        <>
          <PanelResizer
            onResize={setRightPanelWidth}
            minWidth={280}
            maxWidth={480}
          />
          <div
            className="shrink-0 overflow-hidden"
            style={{ width: `${rightPanelWidth}px` }}
          >
            <RightPanel />
          </div>
        </>
      )}
    </div>
  );
}
