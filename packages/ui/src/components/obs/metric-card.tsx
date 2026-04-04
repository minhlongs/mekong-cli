"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Metric-cardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Metric-card = React.forwardRef<HTMLDivElement, Metric-cardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Metric Card</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Single metric with sparkline and threshold</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Metric-card.displayName = "Metric-card";
export { Metric-card };
