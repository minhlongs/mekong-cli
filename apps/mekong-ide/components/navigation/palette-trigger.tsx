interface PaletteTriggerProps {
  onOpenPalette?: () => void;
}

export function PaletteTrigger({ onOpenPalette }: PaletteTriggerProps) {
  return (
    <button
      onClick={onOpenPalette}
      title="Open command palette (Cmd+K)"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.375rem",
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.375rem",
        padding: "0.125rem 0.5rem",
        cursor: "pointer",
        color: "var(--text-muted)",
        fontSize: "0.75rem",
        flexShrink: 0,
        transition: "border-color 0.1s",
      }}
    >
      <span style={{ fontSize: "0.7rem" }}>Search commands…</span>
      <kbd
        style={{
          fontSize: "0.65rem",
          background: "var(--bg-tertiary)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "0.2rem",
          padding: "0.05rem 0.3rem",
          fontFamily: "monospace",
          color: "var(--text-muted)",
        }}
      >
        ⌘K
      </kbd>
    </button>
  );
}
