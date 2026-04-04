"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const findingSeverity = cva("inline-flex items-center rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-bold uppercase", {
  variants: {
    severity: {
      "material-weakness": "bg-[var(--status-error)]/20 text-[var(--status-error)]",
      "significant-deficiency": "bg-[var(--status-warning)]/20 text-[var(--status-warning)]",
      "deficiency": "bg-[var(--status-idle)]/20 text-[var(--text-secondary)]",
    },
  },
  defaultVariants: { severity: "deficiency" },
});

export interface AuditFindingProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  severity: "material-weakness" | "significant-deficiency" | "deficiency";
  owner: string;
  dueDate: string;
  description: string;
}

const AuditFinding = React.forwardRef<HTMLDivElement, AuditFindingProps>(
  ({ className, title, severity, owner, dueDate, description, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="flex items-center justify-between">
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">{title}</span>
        <span className={findingSeverity({ severity })}>{severity.replace("-", " ")}</span>
      </div>
      <p className="text-[var(--font-sm)] text-[var(--text-secondary)]">{description}</p>
      <div className="flex items-center justify-between border-t border-[var(--border-default)] pt-[var(--spacing-sm)]">
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">Owner: {owner}</span>
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">Due: {dueDate}</span>
      </div>
    </div>
  )
);
AuditFinding.displayName = "AuditFinding";
export { AuditFinding, findingSeverity };
