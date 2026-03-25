"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface CommandItem {
  id: string;
  label: string;
  shortcut?: string;
  group?: string;
}

export interface CommandPaletteProps extends React.HTMLAttributes<HTMLDivElement> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  commands: CommandItem[];
  onSelect: (command: CommandItem) => void;
  placeholder?: string;
}

const CommandPalette = React.forwardRef<HTMLDivElement, CommandPaletteProps>(
  ({ className, open, onOpenChange, commands, onSelect, placeholder = "Type a command...", ...props }, ref) => {
    const [query, setQuery] = React.useState("");
    const inputRef = React.useRef<HTMLInputElement>(null);

    const filtered = React.useMemo(() => {
      if (!query) return commands;
      const q = query.toLowerCase();
      return commands.filter((c) => c.label.toLowerCase().includes(q));
    }, [commands, query]);

    const grouped = React.useMemo(() => {
      const groups: Record<string, CommandItem[]> = {};
      for (const cmd of filtered) {
        const g = cmd.group ?? "Commands";
        (groups[g] ??= []).push(cmd);
      }
      return groups;
    }, [filtered]);

    React.useEffect(() => {
      if (open) {
        setQuery("");
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    }, [open]);

    React.useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "k") {
          e.preventDefault();
          onOpenChange(!open);
        }
        if (e.key === "Escape" && open) onOpenChange(false);
      };
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }, [open, onOpenChange]);

    if (!open) return null;

    return (
      <div className="fixed inset-0 z-[var(--z-modal)] flex items-start justify-center pt-[20vh]">
        <div className="fixed inset-0 bg-black/50" onClick={() => onOpenChange(false)} />
        <div
          className={cn(
            "relative w-full max-w-lg rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--bg-primary)] shadow-[var(--shadow-lg)] overflow-hidden",
            className
          )}
          ref={ref}
          {...props}
        >
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="w-full border-b border-[var(--border-default)] bg-transparent px-4 py-3 text-[var(--font-size-base)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none"
          />
          <div className="max-h-80 overflow-y-auto p-2">
            {Object.entries(grouped).map(([group, items]) => (
              <div key={group}>
                <span className="px-2 py-1 text-[var(--font-size-xs)] font-medium text-[var(--text-tertiary)]">
                  {group}
                </span>
                {items.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={() => { onSelect(cmd); onOpenChange(false); }}
                    className="flex w-full items-center justify-between rounded-[var(--radius-md)] px-2 py-1.5 text-[var(--font-size-sm)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors duration-[var(--duration-fast)]"
                  >
                    <span>{cmd.label}</span>
                    {cmd.shortcut && (
                      <kbd className="rounded border border-[var(--border-default)] bg-[var(--bg-secondary)] px-1.5 py-0.5 font-mono text-[0.625rem] text-[var(--text-tertiary)]">
                        {cmd.shortcut}
                      </kbd>
                    )}
                  </button>
                ))}
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="px-2 py-4 text-center text-[var(--font-size-sm)] text-[var(--text-tertiary)]">
                No commands found
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }
);
CommandPalette.displayName = "CommandPalette";

export { CommandPalette };
