"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const testStatusVariants = cva("inline-flex items-center rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: {
    status: {
      passed: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]",
      failed: "bg-[var(--status-error)]/15 text-[var(--status-error)]",
      pending: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]",
      "not-tested": "bg-[var(--status-idle)]/15 text-[var(--status-idle)]",
    },
  },
  defaultVariants: { status: "not-tested" },
});

export interface ControlCardProps extends React.HTMLAttributes<HTMLDivElement> {
  controlId: string;
  name: string;
  owner: string;
  testStatus: "passed" | "failed" | "pending" | "not-tested";
  lastTested?: string;
}

const ControlCard = React.forwardRef<HTMLDivElement, ControlCardProps>(
  ({ className, controlId, name, owner, testStatus, lastTested, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center justify-between rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] px-[var(--spacing-lg)] py-[var(--spacing-md)]", className)} {...props}>
      <div className="flex flex-col gap-[var(--spacing-xs)]">
        <div className="flex items-center gap-[var(--spacing-sm)]">
          <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)]">{controlId}</span>
          <span className="text-[var(--font-sm)] font-medium text-[var(--text-primary)]">{name}</span>
        </div>
        <span className="text-[var(--font-xs)] text-[var(--text-secondary)]">Owner: {owner}</span>
      </div>
      <div className="flex items-center gap-[var(--spacing-md)]">
        {lastTested && <span className="text-[var(--font-xs)] text-[var(--text-muted)]">{lastTested}</span>}
        <span className={testStatusVariants({ status: testStatus })}>{testStatus}</span>
      </div>
    </div>
  )
);
ControlCard.displayName = "ControlCard";
export { ControlCard, testStatusVariants };
