"use client";
/**
 * ResourceBar — horizontal progress bar with adaptive color thresholds.
 * Green <60%, Yellow 60-80%, Red >80%.
 */

interface ResourceBarProps {
  label: string;
  value: number; // 0-100
}

function getBarColor(v: number): string {
  if (v >= 80) return "var(--status-danger)";
  if (v >= 60) return "var(--status-warning)";
  return "var(--accent-teal-500)";
}

export function ResourceBar({ label, value }: ResourceBarProps) {
  const clamped = Math.min(100, Math.max(0, value));
  const color = getBarColor(clamped);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", fontWeight: 500 }}>
          {label}
        </span>
        <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
          {clamped}%
        </span>
      </div>
      <div
        style={{
          height: "0.3rem",
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
            transition: "width 0.4s ease, background 0.3s",
          }}
        />
      </div>
    </div>
  );
}
