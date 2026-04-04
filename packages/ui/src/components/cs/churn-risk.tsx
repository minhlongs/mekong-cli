"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Churn-riskProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Churn-risk = React.forwardRef<HTMLDivElement, Churn-riskProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Churn Risk</div>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-muted)]">{label || "Component ready"}</div>
  </div>
));
Churn-risk.displayName = "Churn-risk";
export { Churn-risk };
