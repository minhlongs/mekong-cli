"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const phaseStatus = cva("flex h-8 w-8 items-center justify-center rounded-full text-[var(--font-xs)] font-bold", {
  variants: { status: { done: "bg-[var(--status-healthy)] text-[var(--bg-primary)]", active: "bg-[var(--accent-teal-500)] text-[var(--bg-primary)] animate-pulse", pending: "bg-[var(--bg-tertiary)] text-[var(--text-muted)]" } },
  defaultVariants: { status: "pending" },
});
export interface Milestone { name: string; date: string; status: "done" | "active" | "pending"; }
export interface MilestoneTrackProps extends React.HTMLAttributes<HTMLDivElement> { milestones: Milestone[]; }
const MilestoneTrack = React.forwardRef<HTMLDivElement, MilestoneTrackProps>(({ className, milestones, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="mb-[var(--spacing-md)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">IPO Milestones</div>
    <div className="flex items-center">{milestones.map((m, i) => (<React.Fragment key={i}><div className="flex flex-col items-center gap-[var(--spacing-xs)]"><span className={phaseStatus({ status: m.status })}>{m.status === "done" ? "\u2713" : i + 1}</span><span className="text-[var(--font-xs)] text-[var(--text-secondary)] whitespace-nowrap">{m.name}</span><span className="text-[var(--font-xs)] text-[var(--text-muted)]">{m.date}</span></div>{i < milestones.length - 1 && <div className={cn("h-0.5 flex-1 mx-1 min-w-[16px]", m.status === "done" ? "bg-[var(--status-healthy)]" : "bg-[var(--border-default)]")} />}</React.Fragment>))}</div>
  </div>
));
MilestoneTrack.displayName = "MilestoneTrack";
export { MilestoneTrack };
