"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface ActivityItem {
  id: string;
  timestamp: string;
  actionType: "buy" | "sell" | "hedge" | "rebalance";
  description: string;
  amount?: number;
}

export interface ActivityFeedProps extends React.HTMLAttributes<HTMLDivElement> {
  items: ActivityItem[];
  maxItems?: number;
}

const actionColors: Record<string, string> = {
  buy: "bg-[var(--color-gain)]/15 text-[var(--color-gain)]",
  sell: "bg-[var(--color-loss)]/15 text-[var(--color-loss)]",
  hedge: "bg-[var(--color-info-500)]/15 text-[var(--color-info-500)]",
  rebalance: "bg-[var(--color-warning-500)]/15 text-[var(--color-warning-500)]",
};

const ActivityFeed = React.forwardRef<HTMLDivElement, ActivityFeedProps>(
  ({ className, items, maxItems = 20, ...props }, ref) => (
    <div
      className={cn(
        "flex flex-col overflow-y-auto rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)]",
        className
      )}
      ref={ref}
      {...props}
    >
      <div className="sticky top-0 border-b border-[var(--border-default)] bg-[var(--bg-primary)] px-4 py-2">
        <span className="text-[var(--font-size-sm)] font-medium text-[var(--text-secondary)]">Activity</span>
      </div>
      {items.slice(0, maxItems).map((item) => (
        <div key={item.id} className="flex items-center gap-3 border-b border-[var(--border-default)] px-4 py-2.5 last:border-0">
          <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)] tabular-nums whitespace-nowrap">
            {item.timestamp}
          </span>
          <span className={cn(
            "rounded-[var(--radius-full)] px-2 py-0.5 text-[0.625rem] font-semibold uppercase",
            actionColors[item.actionType]
          )}>
            {item.actionType}
          </span>
          <span className="flex-1 truncate text-[var(--font-size-sm)] text-[var(--text-primary)]">
            {item.description}
          </span>
          {item.amount !== undefined && (
            <span className="font-mono text-[var(--font-size-sm)] text-[var(--text-secondary)]">
              ${item.amount.toLocaleString()}
            </span>
          )}
        </div>
      ))}
    </div>
  )
);
ActivityFeed.displayName = "ActivityFeed";

export { ActivityFeed };
