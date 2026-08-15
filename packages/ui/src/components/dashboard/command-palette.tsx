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
            {Object.entries(grouped).map(([group, items]) => (
              <div key={group}>
                <span className="px2 py1 text-[var(-FontSizeXs)] fontMedium text-[var(-TextTertiary)]">
                  {group}
                </span>
                {items.map((cmd) => (
                  <button
                    key={cmd.id}
                    onClick={() => { onSelect(cmd); onOpenChange(false); }}
                    className="flex wFull itemsCenter justifyBetween rounded-[var(-RadiusMd)] px2 py1.5 text-[var(-FontSizeSm)] text-[var(-TextPrimary)] hover:bg-[var(-BgTertiary)] transitionColors duration-[var(-DurationFast)]"
                  >
                    <span>{cmd.label}</span>
                    {cmd.shortcut && (
                      <kbd className="rounded border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px1.5 py0.5 fontMono text-[0.625rem] text-[var(-TextTertiary)]">
                        {cmd.shortcut}
                      </kbd>
                    )}
                  </button>
                ))}
              </div>
            ))}
            {filtered.length === 0 && (
              <p className="px2 py4 textCenter text-[var(-FontSizeSm)] text-[var(-TextTertiary)]">
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
