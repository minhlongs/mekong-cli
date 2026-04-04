"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const vulnSeverityVariants = cva(
  "inline-flex items-center rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-bold uppercase tracking-wider",
  {
    variants: {
      severity: {
        critical: "bg-[var(--status-error)]/20 text-[var(--status-error)]",
        high: "bg-[var(--status-warning)]/20 text-[var(--status-warning)]",
        medium: "bg-[var(--accent-teal-500)]/20 text-[var(--accent-teal-400)]",
        low: "bg-[var(--status-idle)]/20 text-[var(--status-idle)]",
      },
    },
    defaultVariants: { severity: "medium" },
  }
);

export interface VulnCardProps extends React.HTMLAttributes<HTMLDivElement> {
  cve: string;
  severity: "critical" | "high" | "medium" | "low";
  component: string;
  slaHours: number;
  status: string;
}

const VulnCard = React.forwardRef<HTMLDivElement, VulnCardProps>(
  ({ className, cve, severity, component, slaHours, status, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]",
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">
          {cve}
        </span>
        <span className={vulnSeverityVariants({ severity })}>{severity}</span>
      </div>
      <span className="text-[var(--font-sm)] text-[var(--text-secondary)]">
        {component}
      </span>
      <div className="flex items-center justify-between border-t border-[var(--border-default)] pt-[var(--spacing-sm)]">
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">
          SLA: {slaHours}h
        </span>
        <span className="text-[var(--font-xs)] font-medium text-[var(--text-secondary)]">
          {status}
        </span>
      </div>
    </div>
  )
);
VulnCard.displayName = "VulnCard";

export { VulnCard, vulnSeverityVariants };
