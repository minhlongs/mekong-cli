"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Alert-ruleProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Alert-rule = React.forwardRef<HTMLDivElement, Alert-ruleProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Alert Rule</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Alert rule with condition and routing</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Alert-rule.displayName = "Alert-rule";
export { Alert-rule };
