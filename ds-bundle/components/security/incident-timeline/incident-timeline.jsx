// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/security/incident-timeline.tsx
// Bundled in _ds_bundle.js as window.IncidentTimeline

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const stepIndicator = cva(
  "flex h8 w8 itemsCenter justifyCenter roundedFull text-[var(-FontXs)] fontBold",
  {
    variants: {
      status: {
        done: "bg-[var(-StatusHealthy)] text-[var(-BgPrimary)]",
        active: "bg-[var(-AccentTeal500)] text-[var(-BgPrimary)] animatePulse",
        pending: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]",
      },
    },
    defaultVariants: { status: "pending" },
  }
);

const stepLine = cva("h0.5 flex1", {
  variants: {
    status: {
      done: "bg-[var(-StatusHealthy)]",
      active: "bg-[var(-AccentTeal500)]",
      pending: "bg-[var(-BorderDefault)]",
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
        "rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]",
        className
      )}
      {...props}
    >
      <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">
        Incident Response Pipeline
      </div>
      <div className="flex itemsCenter">
        {steps.map((step, i) => (
          <React.Fragment key={i}>
            <div className="flex flexCol itemsCenter gap-[var(-SpacingXs)]">
              <span className={stepIndicator({ status: step.status })}>
                {step.status === "done" ? "\u2713" : i + 1}
              </span>
              <span className="text-[var(-FontXs)] text-[var(-TextSecondary)] whitespaceNowrap">
                {step.name}
              </span>
              {step.duration && (
                <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">
                  {step.duration}
                </span>
              )}
            </div>
            {i < steps.length - 1 && (
              <div className={cn(stepLine({ status: step.status }), "mx1 minW-[24px]")} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
);
IncidentTimeline.displayName = "IncidentTimeline";