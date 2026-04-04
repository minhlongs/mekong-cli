"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface BoardCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  date: string;
  attendees: number;
  materialsReady: boolean;
  actionItems: number;
}

const BoardCard = React.forwardRef<HTMLDivElement, BoardCardProps>(
  ({ className, title, date, attendees, materialsReady, actionItems, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
      <div className="flex items-center justify-between">
        <span className="text-[var(--font-md)] font-semibold text-[var(--text-primary)]">{title}</span>
        <span className="text-[var(--font-xs)] text-[var(--text-muted)]">{date}</span>
      </div>
      <div className="flex items-center gap-[var(--spacing-lg)] text-[var(--font-xs)]">
        <span className="text-[var(--text-secondary)]">{attendees} attendees</span>
        <span className={materialsReady ? "text-[var(--status-healthy)]" : "text-[var(--status-warning)]"}>
          Materials: {materialsReady ? "Ready" : "Pending"}
        </span>
        <span className="text-[var(--text-secondary)]">{actionItems} action items</span>
      </div>
    </div>
  )
);
BoardCard.displayName = "BoardCard";
export { BoardCard };
