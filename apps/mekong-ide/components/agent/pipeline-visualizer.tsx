// Horizontal pipeline step flow: Plan → Execute → Verify

import { PipelineStepItem } from "./pipeline-step";
import type { PipelineStep } from "@/lib/agent-types";

interface PipelineVisualizerProps {
  steps: PipelineStep[];
}

export function PipelineVisualizer({ steps }: PipelineVisualizerProps) {
  return (
    <div
      style={{
        padding: "0.5rem 0.75rem",
        background: "var(--bg-primary)",
        borderBottom: "1px solid var(--border-subtle)",
        display: "flex",
        alignItems: "center",
        gap: "0.125rem",
        flexWrap: "wrap",
      }}
    >
      <span
        style={{
          fontSize: "0.65rem",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginRight: "0.5rem",
          fontWeight: 600,
        }}
      >
        Pipeline
      </span>
      {steps.map((step, i) => (
        <PipelineStepItem key={step.id} step={step} isLast={i === steps.length - 1} />
      ))}
    </div>
  );
}
