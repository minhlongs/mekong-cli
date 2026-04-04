"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Oncall-rosterProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Oncall-roster = React.forwardRef<HTMLDivElement, Oncall-rosterProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">On-Call Roster</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Current on-call rotation and schedule</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Oncall-roster.displayName = "Oncall-roster";
export { Oncall-roster };
