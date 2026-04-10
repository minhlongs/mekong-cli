type RiskLevel = "low" | "medium" | "high" | "critical";

interface PermissionDetailRowProps {
  label: string;
  value: string;
  riskLevel?: RiskLevel;
}

const RISK_COLORS: Record<RiskLevel, string> = {
  low: "var(--status-success)",
  medium: "var(--status-warning)",
  high: "var(--status-danger)",
  critical: "#ff2d2d",
};

/**
 * Label + value row inside the permission dialog.
 * If riskLevel is set, renders a colored dot before the value.
 */
export function PermissionDetailRow({ label, value, riskLevel }: PermissionDetailRowProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.375rem 0",
      }}
    >
      <span
        style={{
          minWidth: "90px",
          fontSize: "0.8rem",
          color: "var(--text-muted)",
          fontWeight: 500,
          flexShrink: 0,
        }}
      >
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
        {riskLevel && (
          <span
            title={riskLevel}
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: RISK_COLORS[riskLevel],
              flexShrink: 0,
            }}
          />
        )}
        <span
          style={{
            fontSize: "0.85rem",
            color: riskLevel ? RISK_COLORS[riskLevel] : "var(--text-primary)",
            fontWeight: riskLevel ? 600 : 400,
          }}
        >
          {value}
        </span>
      </div>
    </div>
  );
}
