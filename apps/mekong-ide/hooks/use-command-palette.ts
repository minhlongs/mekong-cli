"use client";

import { useState, useCallback, useMemo } from "react";
import { useKeyboardShortcuts } from "./use-keyboard-shortcuts";

export interface PaletteCommand {
  id: string;
  label: string;
  description?: string;
  shortcut?: string;
  icon?: string;
  category: "navigation" | "editor" | "tools" | "view";
  action: () => void;
}

interface UseCommandPaletteReturn {
  isOpen: boolean;
  search: string;
  selectedIndex: number;
  filteredCommands: PaletteCommand[];
  open: () => void;
  close: () => void;
  setSearch: (q: string) => void;
  selectNext: () => void;
  selectPrev: () => void;
  executeSelected: () => void;
}

/** Fuzzy-ish filter: all search words must appear in label or description */
function filterCommands(commands: PaletteCommand[], query: string): PaletteCommand[] {
  const q = query.trim().toLowerCase();
  if (!q) return commands;
  const words = q.split(/\s+/);
  return commands.filter((cmd) => {
    const haystack = `${cmd.label} ${cmd.description ?? ""}`.toLowerCase();
    return words.every((w) => haystack.includes(w));
  });
}

export function useCommandPalette(commands: PaletteCommand[]): UseCommandPaletteReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearchRaw] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filteredCommands = useMemo(
    () => filterCommands(commands, search),
    [commands, search]
  );

  const open = useCallback(() => {
    setIsOpen(true);
    setSearchRaw("");
    setSelectedIndex(0);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    setSearchRaw("");
    setSelectedIndex(0);
  }, []);

  const setSearch = useCallback((q: string) => {
    setSearchRaw(q);
    setSelectedIndex(0);
  }, []);

  const selectNext = useCallback(() => {
    setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
  }, [filteredCommands.length]);

  const selectPrev = useCallback(() => {
    setSelectedIndex((i) => Math.max(i - 1, 0));
  }, []);

  const executeSelected = useCallback(() => {
    const cmd = filteredCommands[selectedIndex];
    if (cmd) {
      close();
      cmd.action();
    }
  }, [filteredCommands, selectedIndex, close]);

  // Global Cmd+K to open
  useKeyboardShortcuts([{ key: "cmd+k", callback: open }]);

  return {
    isOpen,
    search,
    selectedIndex,
    filteredCommands,
    open,
    close,
    setSearch,
    selectNext,
    selectPrev,
    executeSelected,
  };
}
