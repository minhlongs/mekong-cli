"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const stepIndicator = cva(
  "flex h-8 w-8 items-center justify-center rounded-full text-[var(--font-xs)] font-bold",
  {
    variants: {
      status: {
        done: "bg-[var(--status-healthy)] text-[var(--bg-primary)]",
        active: "bg-[var(--accent-teal-500)] text-[var(--bg-primary)] animate-pulse",
        pending: "bg-[var(--bg-tertiary)] text-[var(--text-muted)]",
      },
    },
    defaultVariants: { status: "pending" },
  }
);

const stepLine = cva("h-0.5 flex-1", {
  variants: {
    status: {
      done: "bg-[var(--status-healthy)]",
      active: "bg-[var(--accent-teal-500)]",
      pending: "bg-[var(--border-default)]",
    },
  },
  defaultVariants: { status: "pending" },
});

export interface TimelineStep {
  name: string;
  status: "done" | "active" | "pending";
  duration?: string;
}

export interface IncidentTimelineProps extends React.HTMLAttributes<HTMLDivElement> {
  steps: TimelineStep[];
}

const IncidentTimeline = React.forwardRef<HTMLDivElement, IncidentTimelineProps>(
  ({ className, steps, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]",
        className
      )}
      {...props}
    >
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">
        Incident Response Pipeline
      </div>
      <div className="flex items-center">
        {steps.map((step, i) => (
          <React.Fragment key={i}>
            <div className="flex flex-col items-center gap-[var(--spacing-xs)]">
              <span className={stepIndicator({ status: step.status })}>
                {step.status === "done" ? "\u2713" : i + 1}
              </span>
              <span className="text-[var(--font-xs)] text-[var(--text-secondary)] whitespace-nowrap">
                {step.name}
              </span>
              {step.duration && (
                <span className="text-[var(--font-xs)] text-[var(--text-muted)]">
                  {step.duration}
                </span>
              )}
            </div>
            {i < steps.length - 1 && (
              <div className={cn(stepLine({ status: step.status }), "mx-1 min-w-[24px]")} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
);
IncidentTimeline.displayName = "IncidentTimeline";

export { IncidentTimeline };
