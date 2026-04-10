// Single step in the pipeline visualizer flow

import { Check, Loader2, X, Circle } from "lucide-react";
import type { PipelineStep } from "@/lib/agent-types";

interface PipelineStepProps {
  step: PipelineStep;
  isLast?: boolean;
}

const statusIcon = {
  pending: <Circle size={14} style={{ color: "var(--text-muted)" }} />,
  active: <Loader2 size={14} className="animate-spin" style={{ color: "var(--accent-teal-400)" }} />,
  done: <Check size={14} style={{ color: "var(--status-success)" }} />,
  error: <X size={14} style={{ color: "var(--status-danger)" }} />,
};

const statusColor: Record<PipelineStep["status"], string> = {
  pending: "var(--text-muted)",
  active: "var(--accent-teal-400)",
  done: "var(--status-success)",
  error: "var(--status-danger)",
};

export function PipelineStepItem({ step, isLast = false }: PipelineStepProps) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
      {/* Icon + label */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "2px" }}>
        <div
          style={{
            width: "1.5rem",
            height: "1.5rem",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: step.status === "active" ? "rgba(45,212,191,0.1)" : "var(--surface-card)",
            border: `1px solid ${step.status === "pending" ? "var(--border-subtle)" : statusColor[step.status]}`,
          }}
        >
          {statusIcon[step.status]}
        </div>
      </div>

      {/* Label */}
      <span
        style={{
          fontSize: "0.7rem",
          fontWeight: step.status === "active" ? 600 : 400,
          color: statusColor[step.status],
          minWidth: "3rem",
        }}
      >
        {step.label}
        {step.duration && (
          <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>
            {" "}
            {step.duration}ms
          </span>
        )}
      </span>

      {/* Arrow connector */}
      {!isLast && (
        <span style={{ color: "var(--border-strong)", fontSize: "0.65rem", margin: "0 2px" }}>
          →
        </span>
      )}
    </div>
  );
}
