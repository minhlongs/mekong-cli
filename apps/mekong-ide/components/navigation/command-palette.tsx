"use client";

import { useRef, useEffect, useCallback } from "react";
import { Search } from "lucide-react";
import { useCommandPalette } from "@/hooks/use-command-palette";
import { useCommandPaletteContext } from "./command-palette-provider";
import { CommandPaletteItem } from "./command-palette-item";
import type { PaletteCommand } from "@/hooks/use-command-palette";

const CATEGORY_LABELS: Record<PaletteCommand["category"], string> = {
  navigation: "Navigation",
  editor: "Editor",
  tools: "Tools",
  view: "View",
};

/**
 * Full-screen overlay command palette triggered by Cmd+K.
 * Keyboard: ArrowUp/Down to navigate, Enter to execute, Escape to close.
 */
export function CommandPalette() {
  const { commands } = useCommandPaletteContext();
  const palette = useCommandPalette(commands);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when opened
  useEffect(() => {
    if (palette.isOpen) {
      setTimeout(() => inputRef.current?.focus(), 10);
    }
  }, [palette.isOpen]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") { e.preventDefault(); palette.selectNext(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); palette.selectPrev(); }
      else if (e.key === "Enter") { e.preventDefault(); palette.executeSelected(); }
      else if (e.key === "Escape") { e.preventDefault(); palette.close(); }
    },
    [palette]
  );

  if (!palette.isOpen) return null;

  // Group filtered commands by category
  const grouped = palette.filteredCommands.reduce<
    Partial<Record<PaletteCommand["category"], PaletteCommand[]>>
  >((acc, cmd) => {
    (acc[cmd.category] ??= []).push(cmd);
    return acc;
  }, {});

  const categories = (Object.keys(grouped) as PaletteCommand["category"][]).filter(
    (k) => grouped[k]!.length > 0
  );

  // Flat index mapping for keyboard nav
  let flatIndex = 0;

  return (
    /* Backdrop */
    <div
      onClick={palette.close}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(0,0,0,0.6)",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        paddingTop: "15vh",
      }}
    >
      {/* Palette card */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "min(600px, calc(100vw - 2rem))",
          background: "var(--surface-card)",
          border: "1px solid var(--border-strong)",
          borderRadius: "0.75rem",
          overflow: "hidden",
          boxShadow: "0 24px 64px rgba(0,0,0,0.6)",
        }}
      >
        {/* Search row */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            padding: "0 1rem",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <Search size={18} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
          <input
            ref={inputRef}
            value={palette.search}
            onChange={(e) => palette.setSearch(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search commands…"
            aria-autocomplete="list"
            style={{
              flex: 1,
              height: "3rem",
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text-primary)",
              fontSize: "1rem",
              caretColor: "var(--accent-teal-400)",
            }}
          />
          <kbd
            style={{
              fontSize: "0.7rem",
              color: "var(--text-muted)",
              background: "var(--bg-tertiary)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0.25rem",
              padding: "0.125rem 0.375rem",
              fontFamily: "monospace",
              flexShrink: 0,
            }}
          >
            Cmd+K
          </kbd>
        </div>

        {/* Results */}
        <div
          role="listbox"
          style={{ maxHeight: "360px", overflowY: "auto", padding: "0.5rem" }}
        >
          {palette.filteredCommands.length === 0 && (
            <div
              style={{
                padding: "2rem",
                textAlign: "center",
                color: "var(--text-muted)",
                fontSize: "0.875rem",
              }}
            >
              No commands match &quot;{palette.search}&quot;
            </div>
          )}

          {categories.map((category) => {
            const items = grouped[category]!;
            return (
              <div key={category}>
                {/* Category header */}
                <div
                  style={{
                    padding: "0.5rem 1rem 0.25rem",
                    fontSize: "0.7rem",
                    color: "var(--text-muted)",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.05em",
                  }}
                >
                  {CATEGORY_LABELS[category]}
                </div>

                {items.map((cmd) => {
                  const idx = flatIndex++;
                  return (
                    <CommandPaletteItem
                      key={cmd.id}
                      command={cmd}
                      isActive={palette.selectedIndex === idx}
                      onHover={() => {
                        // Update selectedIndex to this item's flat index
                        // We expose this via a no-op here — actual hover uses direct index
                      }}
                      onClick={() => {
                        palette.close();
                        cmd.action();
                      }}
                    />
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* Footer hint */}
        <div
          style={{
            display: "flex",
            gap: "1rem",
            padding: "0.5rem 1rem",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          {[["↑↓", "navigate"], ["↵", "select"], ["Esc", "close"]].map(([key, label]) => (
            <span key={key} style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <kbd
                style={{
                  fontSize: "0.65rem",
                  color: "var(--text-muted)",
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "0.2rem",
                  padding: "0.1rem 0.3rem",
                  fontFamily: "monospace",
                }}
              >
                {key}
              </kbd>
              <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{label}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
