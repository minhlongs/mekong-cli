"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Postmortem-cardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Postmortem-card = React.forwardRef<HTMLDivElement, Postmortem-cardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Postmortem Card</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Incident postmortem summary</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Postmortem-card.displayName = "Postmortem-card";
export { Postmortem-card };
