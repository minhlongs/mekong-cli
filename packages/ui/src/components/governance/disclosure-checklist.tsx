"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface DisclosureItem { requirement: string; status: "complete" | "in-progress" | "not-started"; deadline: string; }
export interface DisclosureChecklistProps extends React.HTMLAttributes<HTMLDivElement> { items: DisclosureItem[]; }

const statusIcon = { complete: "\u2713", "in-progress": "\u25CB", "not-started": "\u2014" };
const statusClass = { complete: "text-[var(--status-healthy)]", "in-progress": "text-[var(--status-warning)]", "not-started": "text-[var(--text-muted)]" };

const DisclosureChecklist = React.forwardRef<HTMLDivElement, DisclosureChecklistProps>(
  ({ className, items, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden", className)} {...props}>
      <div className="border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]">
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">SEC Disclosure Checklist</span>
      </div>
      {items.map((item, i) => (
        <div key={i} className="flex items-center justify-between border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-md)] last:border-b-0 hover:bg-[var(--surface-hover)]">
          <div className="flex items-center gap-[var(--spacing-md)]">
            <span className={cn("font-bold", statusClass[item.status])}>{statusIcon[item.status]}</span>
            <span className="text-[var(--font-sm)] text-[var(--text-primary)]">{item.requirement}</span>
          </div>
          <span className="text-[var(--font-xs)] text-[var(--text-muted)]">{item.deadline}</span>
        </div>
      ))}
    </div>
  )
);
DisclosureChecklist.displayName = "DisclosureChecklist";
export { DisclosureChecklist };
