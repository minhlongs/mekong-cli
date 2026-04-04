"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const laneBg = cva("rounded-[var(--radius-lg)] border p-[var(--spacing-lg)]", {
  variants: {
    lane: {
      now: "border-[var(--status-healthy)]/30 bg-[var(--status-healthy)]/5",
      next: "border-[var(--status-warning)]/30 bg-[var(--status-warning)]/5",
      later: "border-[var(--border-default)] bg-[var(--surface-card)]",
    },
  },
  defaultVariants: { lane: "later" },
});

export interface RoadmapItem { title: string; score: number; tag: string; }
export interface RoadmapLaneProps extends React.HTMLAttributes<HTMLDivElement> {
  lane: "now" | "next" | "later";
  items: RoadmapItem[];
}

const RoadmapLane = React.forwardRef<HTMLDivElement, RoadmapLaneProps>(
  ({ className, lane, items, ...props }, ref) => (
    <div ref={ref} className={cn(laneBg({ lane }), className)} {...props}>
      <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-bold uppercase tracking-wider text-[var(--text-secondary)]">{lane}</div>
      <div className="flex flex-col gap-[var(--spacing-sm)]">
        {items.map((item, i) => (
          <div key={i} className="flex items-center justify-between rounded-[var(--radius-md)] bg-[var(--bg-primary)]/50 px-[var(--spacing-md)] py-[var(--spacing-sm)]">
            <span className="text-[var(--font-sm)] text-[var(--text-primary)]">{item.title}</span>
            <div className="flex items-center gap-[var(--spacing-sm)]">
              <span className="rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[var(--font-xs)] text-[var(--text-muted)]">{item.tag}</span>
              <span className="font-mono text-[var(--font-xs)] text-[var(--accent-teal-400)]">{item.score}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
);
RoadmapLane.displayName = "RoadmapLane";
export { RoadmapLane };
