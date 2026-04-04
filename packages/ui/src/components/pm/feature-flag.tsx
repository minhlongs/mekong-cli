"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface FeatureFlagProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  enabled: boolean;
  rolloutPct: number;
  environment: "production" | "staging" | "development";
}

const FeatureFlag = React.forwardRef<HTMLDivElement, FeatureFlagProps>(
  ({ className, name, enabled, rolloutPct, environment, ...props }, ref) => (
    <div ref={ref} className={cn("flex items-center justify-between rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] px-[var(--spacing-lg)] py-[var(--spacing-md)]", className)} {...props}>
      <div className="flex items-center gap-[var(--spacing-md)]">
        <div className={cn("h-3 w-3 rounded-full", enabled ? "bg-[var(--status-healthy)]" : "bg-[var(--status-idle)]")} />
        <span className="font-mono text-[var(--font-sm)] text-[var(--text-primary)]">{name}</span>
      </div>
      <div className="flex items-center gap-[var(--spacing-lg)]">
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">{environment}</span>
        <div className="flex items-center gap-[var(--spacing-sm)]">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-[var(--bg-tertiary)]">
            <div className="h-full rounded-full bg-[var(--accent-teal-500)]" style={{ width: `${rolloutPct}%` }} />
          </div>
          <span className="font-mono text-[var(--font-xs)] text-[var(--text-secondary)]">{rolloutPct}%</span>
        </div>
      </div>
    </div>
  )
);
FeatureFlag.displayName = "FeatureFlag";
export { FeatureFlag };
