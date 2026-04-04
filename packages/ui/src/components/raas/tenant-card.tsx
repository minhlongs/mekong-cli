"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const tierBadge = cva("rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: { tier: { starter: "bg-[var(--status-idle)]/15 text-[var(--status-idle)]", pro: "bg-[var(--accent-teal-500)]/15 text-[var(--accent-teal-400)]", enterprise: "bg-[var(--primary)]/15 text-[var(--primary)]" } },
  defaultVariants: { tier: "starter" },
});
export interface TenantCardProps extends React.HTMLAttributes<HTMLDivElement> { name: string; tier: "starter" | "pro" | "enterprise"; health: number; usage: number; apiCalls: number; }
const TenantCard = React.forwardRef<HTMLDivElement, TenantCardProps>(({ className, name, tier, health, usage, apiCalls, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="flex items-center justify-between"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">{name}</span><span className={tierBadge({ tier })}>{tier}</span></div>
    <div className="grid grid-cols-3 gap-[var(--spacing-sm)] text-[var(--font-xs)]">
      <div className="flex flex-col"><span className="text-[var(--text-muted)]">Health</span><span className={cn("font-mono", health > 90 ? "text-[var(--status-healthy)]" : "text-[var(--status-warning)]")}>{health}%</span></div>
      <div className="flex flex-col"><span className="text-[var(--text-muted)]">Usage</span><span className="font-mono text-[var(--text-primary)]">{usage}%</span></div>
      <div className="flex flex-col"><span className="text-[var(--text-muted)]">API Calls</span><span className="font-mono text-[var(--text-primary)]">{apiCalls.toLocaleString()}</span></div>
    </div>
  </div>
));
TenantCard.displayName = "TenantCard";
export { TenantCard };
