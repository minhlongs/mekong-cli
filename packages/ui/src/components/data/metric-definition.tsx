"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MetricDefinitionProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  definition: string;
  formula: string;
  owner: string;
  lastUpdated: string;
}

const MetricDefinition = React.forwardRef<HTMLDivElement, MetricDefinitionProps>(
  ({ className, name, definition, formula, owner, lastUpdated, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <span className="text-[var(--font-md)] font-semibold text-[var(--text-primary)]">{name}</span>
      <p className="text-[var(--font-sm)] text-[var(--text-secondary)]">{definition}</p>
      <code className="rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] px-[var(--spacing-sm)] py-[var(--spacing-xs)] font-mono text-[var(--font-xs)] text-[var(--accent-teal-400)]">{formula}</code>
      <div className="flex items-center justify-between border-t border-[var(--border-default)] pt-[var(--spacing-sm)]">
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">Owner: {owner}</span>
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">{lastUpdated}</span>
      </div>
    </div>
  )
);
MetricDefinition.displayName = "MetricDefinition";
export { MetricDefinition };
