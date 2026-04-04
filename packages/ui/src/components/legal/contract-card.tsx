"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Contract-cardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Contract-card = React.forwardRef<HTMLDivElement, Contract-cardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Contract Card</div>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-muted)]">{label || "Component ready"}</div>
  </div>
));
Contract-card.displayName = "Contract-card";
export { Contract-card };
