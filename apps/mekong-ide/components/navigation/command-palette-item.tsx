import type { PaletteCommand } from "@/hooks/use-command-palette";

interface CommandPaletteItemProps {
  command: PaletteCommand;
  isActive: boolean;
  onHover: () => void;
  onClick: () => void;
}

const categoryColors: Record<PaletteCommand["category"], string> = {
  navigation: "var(--accent-teal-400)",
  editor: "var(--status-info)",
  tools: "var(--model-reasoning)",
  view: "var(--text-muted)",
};

/**
 * Single row in the command palette list.
 * Highlights when active (keyboard nav or hover).
 */
export function CommandPaletteItem({
  command,
  isActive,
  onHover,
  onClick,
}: CommandPaletteItemProps) {
  return (
    <div
      role="option"
      aria-selected={isActive}
      onMouseEnter={onHover}
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.75rem",
        padding: "0.625rem 1rem",
        cursor: "pointer",
        background: isActive ? "var(--surface-active)" : "transparent",
        borderRadius: "0.375rem",
        transition: "background 0.1s",
      }}
    >
      {/* Icon placeholder / emoji */}
      <span
        style={{
          fontSize: "1rem",
          width: "1.25rem",
          textAlign: "center",
          flexShrink: 0,
        }}
      >
        {command.icon ?? "▸"}
      </span>

      {/* Label + description */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: "0.875rem",
            color: "var(--text-primary)",
            fontWeight: 500,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {command.label}
        </div>
        {command.description && (
          <div
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {command.description}
          </div>
        )}
      </div>

      {/* Category dot */}
      <span
        style={{
          width: "0.375rem",
          height: "0.375rem",
          borderRadius: "50%",
          background: categoryColors[command.category],
          flexShrink: 0,
        }}
      />

      {/* Shortcut badge */}
      {command.shortcut && (
        <kbd
          style={{
            fontSize: "0.7rem",
            color: "var(--text-muted)",
            background: "var(--bg-tertiary)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.25rem",
            padding: "0.125rem 0.375rem",
            fontFamily: "monospace",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          {command.shortcut}
        </kbd>
      )}
    </div>
  );
}
