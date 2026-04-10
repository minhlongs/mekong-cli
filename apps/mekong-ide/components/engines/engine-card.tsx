"use client";
/**
 * EngineCard — single engine: name, model, status, resource bars, controls.
 */
import { Card, Badge } from "@/components/ds";
import { ResourceBar } from "./resource-bar";
import { EngineControls } from "./engine-controls";
import type { Engine, EngineStatus } from "@/lib/types/engine-types";

interface EngineCardProps {
  engine: Engine;
  onStart:   (id: string) => void;
  onStop:    (id: string) => void;
  onRestart: (id: string) => void;
}

const statusBadge: Record<EngineStatus, { variant: "success" | "warning" | "danger" | "info"; label: string }> = {
  running: { variant: "success", label: "Live"    },
  idle:    { variant: "warning", label: "Idle"    },
  stopped: { variant: "danger",  label: "Stopped" },
  error:   { variant: "danger",  label: "Error"   },
};

export function EngineCard({ engine, onStart, onStop, onRestart }: EngineCardProps) {
  const badge = statusBadge[engine.status];

  return (
    <Card>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
        <div>
          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>
            {engine.name}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.1rem" }}>
            {engine.model}
          </div>
        </div>
        <Badge variant={badge.variant} label={badge.label} dot />
      </div>

      {/* Port */}
      <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
        :{engine.port}
      </div>

      {/* Stats row */}
      <div style={{ display: "flex", gap: "1rem", marginBottom: "0.75rem" }}>
        <div>
          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginBottom: "0.15rem" }}>Tokens/s</div>
          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--accent-teal-400)" }}>
            {engine.tokensPerSec > 0 ? engine.tokensPerSec : "—"}
          </div>
        </div>
        <div>
          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginBottom: "0.15rem" }}>Latency</div>
          <div style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-secondary)" }}>
            {engine.latencyMs > 0 ? `${engine.latencyMs}ms` : "—"}
          </div>
        </div>
      </div>

      {/* Resource bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
        <ResourceBar label="RAM" value={engine.resources.ram} />
        <ResourceBar label="GPU" value={engine.resources.gpu} />
      </div>

      {/* Controls */}
      <EngineControls
        engineId={engine.id}
        status={engine.status}
        onStart={onStart}
        onStop={onStop}
        onRestart={onRestart}
      />
    </Card>
  );
}
