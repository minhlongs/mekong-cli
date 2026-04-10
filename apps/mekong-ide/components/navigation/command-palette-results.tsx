import { CommandPaletteItem } from "./command-palette-item";
import type { PaletteCommand } from "@/hooks/use-command-palette";

const CATEGORY_LABELS: Record<PaletteCommand["category"], string> = {
  navigation: "Navigation",
  editor: "Editor",
  tools: "Tools",
  view: "View",
};

interface Props {
  filteredCommands: PaletteCommand[];
  selectedIndex: number;
  search: string;
  onClose: () => void;
}

export function CommandPaletteResults({ filteredCommands, selectedIndex, search, onClose }: Props) {
  const grouped = filteredCommands.reduce<
    Partial<Record<PaletteCommand["category"], PaletteCommand[]>>
  >((acc, cmd) => {
    (acc[cmd.category] ??= []).push(cmd);
    return acc;
  }, {});

  const categories = (Object.keys(grouped) as PaletteCommand["category"][]).filter(
    (k) => grouped[k]!.length > 0
  );

  let flatIndex = 0;

  return (
    <div role="listbox" style={{ maxHeight: "360px", overflowY: "auto", padding: "0.5rem" }}>
      {filteredCommands.length === 0 && (
        <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
          No commands match &quot;{search}&quot;
        </div>
      )}

      {categories.map((category) => {
        const items = grouped[category]!;
        return (
          <div key={category}>
            <div style={{
              padding: "0.5rem 1rem 0.25rem", fontSize: "0.7rem", color: "var(--text-muted)",
              fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em",
            }}>
              {CATEGORY_LABELS[category]}
            </div>
            {items.map((cmd) => {
              const idx = flatIndex++;
              return (
                <CommandPaletteItem
                  key={cmd.id}
                  command={cmd}
                  isActive={selectedIndex === idx}
                  onHover={() => {}}
                  onClick={() => { onClose(); cmd.action(); }}
                />
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
