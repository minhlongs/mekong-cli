"use client";
/**
 * SystemResourcesPanel — segmented RAM bar + GPU utilization bar + legend.
 */
import type { SystemResources } from "@/lib/types/engine-types";

interface SystemResourcesPanelProps {
  system: SystemResources;
}

export function SystemResourcesPanel({ system }: SystemResourcesPanelProps) {
  const ramPercent = Math.round((system.usedRam / system.totalRam) * 100);

  return (
    <div
      style={{
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "0.5rem",
        padding: "1rem",
      }}
    >
      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.75rem" }}>
        System Resources
      </div>

      {/* RAM segmented bar */}
      <div style={{ marginBottom: "0.75rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>RAM</span>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>
            {system.usedRam} / {system.totalRam} GB ({ramPercent}%)
          </span>
        </div>
        {/* Segmented bar */}
        <div style={{ height: "0.5rem", background: "var(--border-subtle)", borderRadius: "9999px", overflow: "hidden", display: "flex" }}>
          {system.ramSegments.map((seg) => (
            <div
              key={seg.engineId}
              title={`${seg.engineName}: ${seg.percent}%`}
              style={{
                height: "100%",
                width: `${seg.percent}%`,
                background: seg.color,
                transition: "width 0.4s ease",
              }}
            />
          ))}
        </div>
        {/* Legend */}
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.4rem", flexWrap: "wrap" }}>
          {system.ramSegments.map((seg) => (
            <div key={seg.engineId} style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <div style={{ width: "0.5rem", height: "0.5rem", borderRadius: "2px", background: seg.color }} />
              <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>{seg.engineName} {seg.percent}%</span>
            </div>
          ))}
        </div>
      </div>

      {/* GPU utilization bar */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
          <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>GPU</span>
          <span style={{ fontSize: "0.7rem", color: "var(--text-secondary)" }}>{system.gpuUtilization}%</span>
        </div>
        <div style={{ height: "0.5rem", background: "var(--border-subtle)", borderRadius: "9999px", overflow: "hidden" }}>
          <div
            style={{
              height: "100%",
              width: `${system.gpuUtilization}%`,
              background: system.gpuUtilization >= 80 ? "var(--status-danger)" : system.gpuUtilization >= 60 ? "var(--status-warning)" : "var(--model-architect)",
              borderRadius: "9999px",
              transition: "width 0.4s ease",
            }}
          />
        </div>
      </div>
    </div>
  );
}
