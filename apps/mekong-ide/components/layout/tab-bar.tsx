"use client";

import { X, Plus } from "lucide-react";
import clsx from "clsx";

export interface TabItem {
  id: string;
  label: string;
  /** File extension for icon color hints */
  ext?: string;
  modified?: boolean;
}

interface TabBarProps {
  tabs: TabItem[];
  activeTabId?: string;
  onTabSelect?: (id: string) => void;
  onTabClose?: (id: string) => void;
  onTabAdd?: () => void;
}

/**
 * Horizontal file tab bar with close buttons. 32px height.
 * Active tab highlighted with surface-active background.
 */
export function TabBar({
  tabs,
  activeTabId,
  onTabSelect,
  onTabClose,
  onTabAdd,
}: TabBarProps) {
  return (
    <div
      className="flex items-center h-8 overflow-x-auto shrink-0 select-none"
      style={{
        backgroundColor: "var(--bg-secondary)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTabId;
        return (
          <div
            key={tab.id}
            className={clsx(
              "group flex items-center gap-1.5 px-3 h-full text-xs cursor-pointer shrink-0",
              "border-r border-[var(--border-subtle)] transition-colors duration-100",
              isActive
                ? "text-[var(--text-primary)] bg-[var(--bg-primary)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-hover)]"
            )}
            onClick={() => onTabSelect?.(tab.id)}
          >
            {tab.modified && (
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-teal-400)] shrink-0" />
            )}
            <span className="max-w-[120px] truncate">{tab.label}</span>
            <button
              className={clsx(
                "ml-0.5 rounded p-0.5 shrink-0 transition-opacity",
                "opacity-0 group-hover:opacity-100",
                isActive && "opacity-100",
                "hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)]"
              )}
              onClick={(e) => {
                e.stopPropagation();
                onTabClose?.(tab.id);
              }}
              aria-label={`Close ${tab.label}`}
            >
              <X size={12} />
            </button>
          </div>
        );
      })}

      {/* New tab button */}
      <button
        className="px-2 h-full flex items-center text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] transition-colors"
        onClick={onTabAdd}
        aria-label="New tab"
      >
        <Plus size={14} />
      </button>
    </div>
  );
}
