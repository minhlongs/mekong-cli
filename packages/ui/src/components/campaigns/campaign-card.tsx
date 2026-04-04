"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const campaignStatus = cva("rounded-[var(--radius-sm)] px-2 py-0.5 text-[var(--font-xs)] font-medium", {
  variants: { status: { active: "bg-[var(--status-healthy)]/15 text-[var(--status-healthy)]", draft: "bg-[var(--status-idle)]/15 text-[var(--status-idle)]", paused: "bg-[var(--status-warning)]/15 text-[var(--status-warning)]", ended: "bg-[var(--bg-tertiary)] text-[var(--text-muted)]" } },
  defaultVariants: { status: "draft" },
});
export interface CampaignCardProps extends React.HTMLAttributes<HTMLDivElement> { name: string; status: "active" | "draft" | "paused" | "ended"; budget: number; roi: number; channels: string[]; }
const CampaignCard = React.forwardRef<HTMLDivElement, CampaignCardProps>(({ className, name, status, budget, roi, channels, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="flex items-center justify-between"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">{name}</span><span className={campaignStatus({ status })}>{status}</span></div>
    <div className="flex items-center gap-[var(--spacing-lg)] text-[var(--font-xs)]"><span className="text-[var(--text-muted)]">${budget.toLocaleString()}</span><span className={cn("font-mono", roi > 0 ? "text-[var(--status-healthy)]" : "text-[var(--status-error)]")}>{roi > 0 ? "+" : ""}{roi}% ROI</span></div>
    <div className="flex gap-[var(--spacing-xs)]">{channels.map((ch) => (<span key={ch} className="rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[var(--font-xs)] text-[var(--text-muted)]">{ch}</span>))}</div>
  </div>
));
CampaignCard.displayName = "CampaignCard";
export { CampaignCard };
