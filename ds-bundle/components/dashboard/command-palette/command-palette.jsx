// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/dashboard/command-palette.tsx
// Bundled in _ds_bundle.js as window.CommandPalette

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface CommandItem {
  id: string;
  label: string;
  shortcut?: string;
  group?: string;
}

export interface CommandPaletteProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'> {
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
      <div className="fixed inset0 z-[var(-ZModal)] flex itemsStart justifyCenter pt-[20vh]">
        <div className="fixed inset0 bgBlack/50" onClick={() => onOpenChange(false)} />
        <div
          className={cn(
            "relative wFull maxWLg rounded-[var(-RadiusXl)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] shadow-[var(-ShadowLg)] overflowHidden",
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
            className="wFull borderB border-[var(-BorderDefault)] bgTransparent px4 py3 text-[var(-FontSizeBase)] text-[var(-TextPrimary)] placeholder:text-[var(-TextTertiary)] outlineNone"
          />
          <div className="maxH80 overflowYAuto p2">