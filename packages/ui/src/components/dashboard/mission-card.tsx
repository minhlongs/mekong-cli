"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface MissionCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  status: "pending" | "running" | "success" | "failed";
  creditCost: number;
  agents?: string[];
  expandable?: boolean;
}

const statusStyles: Record<string, string> = {
  pending: "bg-[var(--bg-tertiary)] text-[var(--text-secondary)]",
  running: "bg-[var(--color-info-500)]/15 text-[var(--color-info-500)]",
  success: "bg-[var(--color-success-500)]/15 text-[var(--color-success-500)]",
  failed: "bg-[var(--color-danger-500)]/15 text-[var(--color-danger-500)]",
};

const MissionCard = React.forwardRef<HTMLDivElement, MissionCardProps>(
  ({ className, title, status, creditCost, agents = [], expandable, children, ...props }, ref) => {
    const [expanded, setExpanded] = React.useState(false);

    return (
      <div
        className={cn(
          "rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] transition-shadow duration-[var(--duration-normal)]",
          status === "running" && "ring-1 ring-[var(--color-info-500)]/30",
          className
        )}
        ref={ref}
        {...props}
      >
        <div
          className={cn("flex items-center gap-3 p-[var(--spacing-4)]", expandable && "cursor-pointer")}
          onClick={expandable ? () => setExpanded(!expanded) : undefined}
        >
          <div className="flex flex-1 flex-col gap-1">
            <span className="text-[var(--font-size-sm)] font-medium text-[var(--text-primary)]">{title}</span>
            <div className="flex items-center gap-2">
              <span className={cn(
                "rounded-[var(--radius-full)] px-2 py-0.5 text-[0.625rem] font-semibold uppercase",
                statusStyles[status]
              )}>
                {status}
              </span>
              <span className="font-mono text-[var(--font-size-xs)] text-[var(--text-tertiary)]">
                {creditCost} MCU
              </span>
            </div>
          </div>
          {agents.length > 0 && (
            <div className="flex -space-x-1">
              {agents.map((agent) => (
                <span
                  key={agent}
                  className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--accent)] text-[0.625rem] font-bold text-[var(--accent-text)]"
                  title={agent}
                >
                  {agent[0]}
                </span>
              ))}
            </div>
          )}
          {expandable && (
            <span className={cn(
              "text-[var(--text-tertiary)] transition-transform duration-[var(--duration-fast)]",
              expanded && "rotate-180"
            )}>
              &#x25BC;
            </span>
          )}
        </div>
        {expandable && expanded && children && (
          <div className="border-t border-[var(--border-default)] p-[var(--spacing-4)]">
            {children}
          </div>
        )}
      </div>
    );
  }
);
MissionCard.displayName = "MissionCard";

export { MissionCard };
