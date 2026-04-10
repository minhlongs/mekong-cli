"use client";
/**
 * EngineFarmPage — full page layout: header, engine grid, queue/router cards, system resources.
 */
import { Badge, Button, Card } from "@/components/ds";
import { EngineCard } from "./engine-card";
import { SystemResourcesPanel } from "./system-resources-panel";
import { useEngines } from "@/hooks/use-engines";
import { MOCK_SYSTEM, MOCK_QUEUE, MOCK_ROUTER } from "@/lib/mock/engine-mock-data";

export function EngineFarmPage() {
  const { engines, start, stop, isLoading, isDemoMode } = useEngines();

  const engineList = engines ?? [];
  const runningCount = engineList.filter((e) => e.status === "running").length;

  return (
    <div style={{ padding: "1.5rem", display: "flex", flexDirection: "column", gap: "1.25rem", minHeight: "100vh", background: "var(--bg-primary)" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <h1 style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text-primary)", margin: 0 }}>
            Engine Farm
          </h1>
          <Badge variant={runningCount > 0 ? "success" : "danger"} label={`${runningCount} running`} dot />
          {isDemoMode && (
            <Badge variant="warning" label="demo" />
          )}
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Button variant="primary" size="sm" onClick={() => engineList.forEach((e) => start(e.id))}>
            Start All
          </Button>
          <Button variant="danger" size="sm" onClick={() => engineList.forEach((e) => stop(e.id))}>
            Stop All
          </Button>
        </div>
      </div>

      {/* Loading state */}
      {isLoading && engineList.length === 0 && (
        <div style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>Loading engines…</div>
      )}

      {/* Row 1 — Engine cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {engineList.map((engine) => (
          <EngineCard
            key={engine.id}
            engine={engine}
            onStart={(id) => start(id)}
            onStop={(id)  => stop(id)}
            onRestart={(id) => { stop(id); setTimeout(() => start(id), 300); }}
          />
        ))}
      </div>

      {/* Row 2 — Queue + Router */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
        <Card header="Request Queue">
          <div style={{ display: "flex", gap: "2rem" }}>
            <Stat label="Pending" value={MOCK_QUEUE.pending} color="var(--status-warning)" />
            <Stat label="Active"  value={MOCK_QUEUE.active}  color="var(--status-success)" />
            <Stat label="Failed"  value={MOCK_QUEUE.failed}  color="var(--status-danger)"  />
          </div>
        </Card>
        <Card header="Model Router">
          <div style={{ display: "flex", gap: "2rem" }}>
            <Stat label="Routed"    value={MOCK_ROUTER.routed}            color="var(--accent-teal-400)" />
            <Stat label="Avg Route" value={`${MOCK_ROUTER.avgRouteMs}ms`} color="var(--text-secondary)" />
            <Stat label="Fallbacks" value={MOCK_ROUTER.fallbacks}         color="var(--status-warning)"  />
          </div>
        </Card>
      </div>

      {/* System Resources */}
      <SystemResourcesPanel system={MOCK_SYSTEM} />
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div>
      <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", marginBottom: "0.2rem" }}>{label}</div>
      <div style={{ fontSize: "1.25rem", fontWeight: 700, color }}>{value}</div>
    </div>
  );
}
