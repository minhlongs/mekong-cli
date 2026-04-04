"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Revenue-chartProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Revenue-chart = React.forwardRef<HTMLDivElement, Revenue-chartProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Revenue</div>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-muted)]">{label || "Component ready"}</div>
  </div>
));
Revenue-chart.displayName = "Revenue-chart";
export { Revenue-chart };
