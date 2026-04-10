"use client";

import { useEffect, useCallback, useRef } from "react";

export interface ShortcutConfig {
  /** e.g. "cmd+k", "ctrl+`", "escape" */
  key: string;
  callback: (e: KeyboardEvent) => void;
  /** Prevent default browser action. Default: true */
  preventDefault?: boolean;
}

function matchesShortcut(e: KeyboardEvent, key: string): boolean {
  const parts = key.toLowerCase().split("+");
  const mainKey = parts[parts.length - 1];
  const needsCmd = parts.includes("cmd") || parts.includes("meta");
  const needsCtrl = parts.includes("ctrl");
  const needsShift = parts.includes("shift");
  const needsAlt = parts.includes("alt");

  if (needsCmd && !e.metaKey) return false;
  if (needsCtrl && !e.ctrlKey) return false;
  if (needsShift && !e.shiftKey) return false;
  if (needsAlt && !e.altKey) return false;

  const pressedKey = e.key.toLowerCase();
  if (mainKey === "escape" && pressedKey !== "escape") return false;
  if (mainKey === "`" && e.key !== "`") return false;
  if (mainKey !== "escape" && mainKey !== "`" && pressedKey !== mainKey) return false;

  return true;
}

/**
 * Register global keyboard shortcuts.
 * Shortcuts are registered on mount and cleaned up on unmount.
 */
export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
  // Keep latest shortcuts ref to avoid stale closures
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    for (const shortcut of shortcutsRef.current) {
      if (matchesShortcut(e, shortcut.key)) {
        if (shortcut.preventDefault !== false) e.preventDefault();
        shortcut.callback(e);
        return;
      }
    }
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}
