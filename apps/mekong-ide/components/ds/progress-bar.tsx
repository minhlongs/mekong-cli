import type { StatusVariant } from "@/lib/types";

interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  variant?: StatusVariant | "accent";
  showPercent?: boolean;
}

const colorMap: Record<string, string> = {
  accent:  "var(--accent-teal-500)",
  success: "var(--status-success)",
  warning: "var(--status-warning)",
  danger:  "var(--status-danger)",
  info:    "var(--status-info)",
};

export function ProgressBar({
  value,
  label,
  variant = "accent",
  showPercent = true,
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value));
  const color = colorMap[variant] ?? colorMap.accent;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
      {(label || showPercent) && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          {label && (
            <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{label}</span>
          )}
          {showPercent && (
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "auto" }}>
              {clamped}%
            </span>
          )}
        </div>
      )}
      <div
        style={{
          height: "0.375rem",
          background: "var(--border-subtle)",
          borderRadius: "9999px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${clamped}%`,
            background: color,
            borderRadius: "9999px",
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}
