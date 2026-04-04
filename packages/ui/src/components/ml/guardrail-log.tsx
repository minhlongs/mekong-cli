"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const triggerBadge = cva("rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: {
    action: {
      blocked: "bg-[var(--status-error)]/15 text-[var(--status-error)]",
      flagged: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]",
      passed: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]",
    },
  },
  defaultVariants: { action: "passed" },
});

export interface GuardrailEvent { time: string; rule: string; action: "blocked" | "flagged" | "passed"; input: string; }
export interface GuardrailLogProps extends React.HTMLAttributes<HTMLDivElement> { events: GuardrailEvent[]; }

const GuardrailLog = React.forwardRef<HTMLDivElement, GuardrailLogProps>(
  ({ className, events, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden", className)} {...props}>
      <div className="border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]">
        <span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Guardrail Log</span>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {events.map((e, i) => (
          <div key={i} className="flex items-center gap-[var(--spacing-md)] border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)] last:border-b-0">
            <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)] min-w-[48px]">{e.time}</span>
            <span className={triggerBadge({ action: e.action })}>{e.action}</span>
            <span className="text-[var(--font-xs)] text-[var(--text-secondary)]">{e.rule}</span>
            <span className="flex-1 truncate text-[var(--font-xs)] text-[var(--text-muted)]">{e.input}</span>
          </div>
        ))}
      </div>
    </div>
  )
);
GuardrailLog.displayName = "GuardrailLog";
export { GuardrailLog };
