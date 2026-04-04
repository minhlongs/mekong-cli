"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Trace-waterfallProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Trace-waterfall = React.forwardRef<HTMLDivElement, Trace-waterfallProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Trace Waterfall</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Distributed trace timeline visualization</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Trace-waterfall.displayName = "Trace-waterfall";
export { Trace-waterfall };
