"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import type { PaletteCommand } from "@/hooks/use-command-palette";

interface CommandPaletteContextValue {
  commands: PaletteCommand[];
  registerCommands: (cmds: PaletteCommand[]) => void;
  unregisterCommands: (ids: string[]) => void;
}

const CommandPaletteContext = createContext<CommandPaletteContextValue | null>(null);

export function CommandPaletteProvider({ children }: { children: ReactNode }) {
  const [commands, setCommands] = useState<PaletteCommand[]>([]);

  const registerCommands = useCallback((cmds: PaletteCommand[]) => {
    setCommands((prev) => {
      // Deduplicate by id — later registration wins
      const ids = new Set(cmds.map((c) => c.id));
      return [...prev.filter((c) => !ids.has(c.id)), ...cmds];
    });
  }, []);

  const unregisterCommands = useCallback((ids: string[]) => {
    const idSet = new Set(ids);
    setCommands((prev) => prev.filter((c) => !idSet.has(c.id)));
  }, []);

  return (
    <CommandPaletteContext.Provider value={{ commands, registerCommands, unregisterCommands }}>
      {children}
    </CommandPaletteContext.Provider>
  );
}

export function useCommandPaletteContext(): CommandPaletteContextValue {
  const ctx = useContext(CommandPaletteContext);
  if (!ctx) throw new Error("useCommandPaletteContext must be inside CommandPaletteProvider");
  return ctx;
}
