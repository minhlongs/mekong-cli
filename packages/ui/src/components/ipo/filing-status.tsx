"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const statusBadge = cva("rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: { status: { filed: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]", drafting: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]", "not-started": "bg-[var(--status-idle)]/15 text-[var(--status-idle)]" } },
  defaultVariants: { status: "not-started" },
});
export interface Filing { name: string; status: "filed" | "drafting" | "not-started"; deadline: string; }
export interface FilingStatusProps extends React.HTMLAttributes<HTMLDivElement> { filings: Filing[]; }
const FilingStatus = React.forwardRef<HTMLDivElement, FilingStatusProps>(({ className, filings, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden", className)} {...props}>
    <div className="border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">SEC Filings</span></div>
    {filings.map((f, i) => (<div key={i} className="flex items-center justify-between border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-md)] last:border-b-0 hover:bg-[var(--surface-hover)]"><span className="text-[var(--font-sm)] text-[var(--text-primary)]">{f.name}</span><div className="flex items-center gap-[var(--spacing-md)]"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">{f.deadline}</span><span className={statusBadge({ status: f.status })}>{f.status}</span></div></div>))}
  </div>
));
FilingStatus.displayName = "FilingStatus";
export { FilingStatus };
