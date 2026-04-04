"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const severityDot = cva("inline-block h-2 w-2 rounded-full", {
  variants: {
    severity: {
      critical: "bg-[var(--status-error)]",
      high: "bg-[var(--status-warning)]",
      medium: "bg-[var(--accent-teal-400)]",
      low: "bg-[var(--status-idle)]",
      info: "bg-[var(--model-qwen)]",
    },
  },
  defaultVariants: { severity: "info" },
});

export interface ThreatEvent {
  time: string;
  type: string;
  source: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
}

export interface ThreatFeedProps extends React.HTMLAttributes<HTMLDivElement> {
  events: ThreatEvent[];
}

const ThreatFeed = React.forwardRef<HTMLDivElement, ThreatFeedProps>(
  ({ className, events, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden",
        className
      )}
      {...props}
    >
      <div className="border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]">
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">
          Threat Feed
        </span>
      </div>
      <div className="flex max-h-80 flex-col overflow-y-auto">
        {events.map((event, i) => (
          <div
            key={i}
            className="flex items-center gap-[var(--spacing-md)] border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)] last:border-b-0 hover:bg-[var(--surface-hover)]"
          >
            <span className={severityDot({ severity: event.severity })} />
            <span className="min-w-[60px] font-mono text-[var(--font-xs)] text-[var(--text-muted)]">
              {event.time}
            </span>
            <span className="flex-1 text-[var(--font-sm)] text-[var(--text-primary)]">
              {event.type}
            </span>
            <span className="text-[var(--font-xs)] text-[var(--text-secondary)]">
              {event.source}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
);
ThreatFeed.displayName = "ThreatFeed";

export { ThreatFeed };
