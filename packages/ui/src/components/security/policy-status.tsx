"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const policyStatusVariants = cva(
  "inline-flex items-center rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium",
  {
    variants: {
      status: {
        active: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]",
        draft: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]",
        expired: "bg-[var(--status-error)]/15 text-[var(--status-error)]",
      },
    },
    defaultVariants: { status: "active" },
  }
);

export interface Policy {
  name: string;
  status: "active" | "draft" | "expired";
  lastReview: string;
}

export interface PolicyStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  policies: Policy[];
}

const PolicyStatus = React.forwardRef<HTMLDivElement, PolicyStatusProps>(
  ({ className, policies, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden",
        className
      )}
      {...props}
    >
      <div className="border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]">
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">
          Policy Compliance
        </span>
      </div>
      <div className="flex flex-col">
        {policies.map((policy, i) => (
          <div
            key={i}
            className="flex items-center justify-between border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-md)] last:border-b-0 hover:bg-[var(--surface-hover)]"
          >
            <span className="text-[var(--font-sm)] text-[var(--text-primary)]">
              {policy.name}
            </span>
            <div className="flex items-center gap-[var(--spacing-md)]">
              <span className="text-[var(--font-xs)] text-[var(--text-muted)]">
                {policy.lastReview}
              </span>
              <span className={policyStatusVariants({ status: policy.status })}>
                {policy.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
);
PolicyStatus.displayName = "PolicyStatus";

export { PolicyStatus, policyStatusVariants };
