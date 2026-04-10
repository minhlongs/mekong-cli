// Model status card: name, provider, latency, status dot

import type { ModelConfig } from "@/lib/agent-types";

interface ModelStatusCardProps {
  model: ModelConfig;
}

const statusDotColor: Record<ModelConfig["status"], string> = {
  online: "var(--status-success)",
  degraded: "var(--status-warning)",
  offline: "var(--status-danger)",
};

const MODEL_COLOR_MAP: Record<string, string> = {
  architect: "var(--model-architect)",
  reasoning: "var(--model-reasoning)",
  audit: "var(--model-audit)",
  trading: "var(--model-trading)",
};

export function ModelStatusCard({ model }: ModelStatusCardProps) {
  const accentColor = MODEL_COLOR_MAP[model.id] ?? "var(--text-secondary)";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.375rem 0.5rem",
        borderRadius: "0.25rem",
        background: "var(--bg-primary)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      {/* Left: dot + name + provider */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
        <span
          style={{
            width: "0.5rem",
            height: "0.5rem",
            borderRadius: "50%",
            background: accentColor,
            flexShrink: 0,
          }}
        />
        <div>
          <div style={{ fontSize: "0.7rem", fontWeight: 500, color: "var(--text-primary)" }}>
            {model.name}
          </div>
          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
            {model.provider}
          </div>
        </div>
      </div>

      {/* Right: latency + status dot */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.375rem" }}>
        <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
          {model.latencyMs}ms
        </span>
        <span
          style={{
            width: "0.4rem",
            height: "0.4rem",
            borderRadius: "50%",
            background: statusDotColor[model.status],
          }}
          title={model.status}
        />
      </div>
    </div>
  );
}
