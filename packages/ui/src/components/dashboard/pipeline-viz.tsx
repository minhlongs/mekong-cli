"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

type StepState = "idle" | "active" | "done" | "failed";

export interface PipelineVizProps extends React.HTMLAttributes<HTMLDivElement> {
  planState?: StepState;
  executeState?: StepState;
  verifyState?: StepState;
}

const stepConfig: Record<string, { label: string; color: string; activeColor: string }> = {
  plan: { label: "Plan", color: "var(--color-info-500)", activeColor: "var(--color-info-500)" },
  execute: { label: "Execute", color: "var(--color-warning-500)", activeColor: "var(--color-warning-500)" },
  verify: { label: "Verify", color: "var(--color-success-500)", activeColor: "var(--color-success-500)" },
};

const stateStyles: Record<StepState, string> = {
  idle: "border-[var(--border-default)] bg-[var(--bg-secondary)] text-[var(--text-tertiary)]",
  active: "ring-2 ring-offset-2 ring-offset-[var(--bg-primary)]",
  done: "opacity-100",
  failed: "border-[var(--color-danger-500)] bg-[var(--color-danger-500)]/10 text-[var(--color-danger-500)]",
};

const PipelineViz = React.forwardRef<HTMLDivElement, PipelineVizProps>(
  ({ className, planState = "idle", executeState = "idle", verifyState = "idle", ...props }, ref) => {
    const steps = [
      { key: "plan", state: planState },
      { key: "execute", state: executeState },
      { key: "verify", state: verifyState },
    ];

    return (
      <div className={cn("flex items-center gap-2", className)} ref={ref} {...props}>
        {steps.map((step, i) => {
          const cfg = stepConfig[step.key];
          return (
            <React.Fragment key={step.key}>
              {i > 0 && (
                <div className={cn(
                  "h-0.5 w-8",
                  step.state === "done" || step.state === "active"
                    ? `bg-[${cfg.color}]`
                    : "bg-[var(--border-default)]"
                )} />
              )}
              <div className={cn(
                "flex items-center gap-1.5 rounded-[var(--radius-full)] border px-3 py-1.5 text-[var(--font-size-xs)] font-semibold",
                stateStyles[step.state],
                step.state === "active" && `ring-[${cfg.activeColor}] border-[${cfg.color}] text-[${cfg.color}]`,
                step.state === "done" && `border-[${cfg.color}] bg-[${cfg.color}]/10 text-[${cfg.color}]`,
              )}>
                {step.state === "active" && (
                  <span className={`h-1.5 w-1.5 animate-pulse rounded-full bg-[${cfg.color}]`} />
                )}
                {step.state === "done" && <span>&#x2713;</span>}
                {step.state === "failed" && <span>&#x2717;</span>}
                {cfg.label}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    );
  }
);
PipelineViz.displayName = "PipelineViz";

export { PipelineViz };
