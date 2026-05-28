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
  plan: { label: "Plan", color: "var(-ColorInfo500)", activeColor: "var(-ColorInfo500)" },
  execute: { label: "Execute", color: "var(-ColorWarning500)", activeColor: "var(-ColorWarning500)" },
  verify: { label: "Verify", color: "var(-ColorSuccess500)", activeColor: "var(-ColorSuccess500)" },
};

const stateStyles: Record<StepState, string> = {
  idle: "border-[var(-BorderDefault)] bg-[var(-BgSecondary)] text-[var(-TextTertiary)]",
  active: "ring2 ringOffset2 ringOffset-[var(-BgPrimary)]",
  done: "opacity100",
  failed: "border-[var(-ColorDanger500)] bg-[var(-ColorDanger500)]/10 text-[var(-ColorDanger500)]",
};

const PipelineViz = React.forwardRef<HTMLDivElement, PipelineVizProps>(
  ({ className, planState = "idle", executeState = "idle", verifyState = "idle", ...props }, ref) => {
    const steps = [
      { key: "plan", state: planState },
      { key: "execute", state: executeState },
      { key: "verify", state: verifyState },
    ];

    return (
      <div className={cn("flex itemsCenter gap2", className)} ref={ref} {...props}>
        {steps.map((step, i) => {
          const cfg = stepConfig[step.key];
          return (
            <React.Fragment key={step.key}>
              {i > 0 && (
                <div className={cn(
                  "h0.5 w8",
                  step.state === "done" || step.state === "active"
                    ? `bg-[${cfg.color}]`
                    : "bg-[var(-BorderDefault)]"
                )} />
              )}
              <div className={cn(
                "flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border px3 py1.5 text-[var(-FontSizeXs)] fontSemibold",
                stateStyles[step.state],
                step.state === "active" && `ring-[${cfg.activeColor}] border-[${cfg.color}] text-[${cfg.color}]`,
                step.state === "done" && `border-[${cfg.color}] bg-[${cfg.color}]/10 text-[${cfg.color}]`,
              )}>
                {step.state === "active" && (
                  <span className={`h1.5 w1.5 animatePulse roundedFull bg-[${cfg.color}]`} />
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
