"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface BotStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  strategy: string;
  status: "online" | "degraded" | "offline";
  uptime: string;
  lastAction: string;
}

const statusConfig = {
  online: { dot: "bg-[var(--color-success-500)]", label: "Online" },
  degraded: { dot: "bg-[var(--color-warning-500)]", label: "Degraded" },
  offline: { dot: "bg-[var(--color-neutral-400)]", label: "Offline" },
};

const BotStatus = React.forwardRef<HTMLDivElement, BotStatusProps>(
  ({ className, name, strategy, status, uptime, lastAction, ...props }, ref) => {
    const config = statusConfig[status];
    return (
      <div
        className={cn(
          "flex items-center gap-[var(--spacing-4)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-[var(--spacing-4)]",
          className
        )}
        ref={ref}
        {...props}
      >
        <div className="relative">
          <span className={cn("block h-3 w-3 rounded-full", config.dot)} />
          {status === "online" && (
            <span className={cn("absolute inset-0 h-3 w-3 animate-ping rounded-full opacity-75", config.dot)} />
          )}
        </div>
        <div className="flex flex-1 flex-col">
          <span className="text-[var(--font-size-sm)] font-semibold text-[var(--text-primary)]">{name}</span>
          <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)]">{strategy}</span>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-[var(--font-size-xs)] text-[var(--text-secondary)]">{uptime}</span>
          <span className="text-[var(--font-size-xs)] text-[var(--text-tertiary)]">{lastAction}</span>
        </div>
      </div>
    );
  }
);
BotStatus.displayName = "BotStatus";

export { BotStatus };
