"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface ChannelCardProps extends React.HTMLAttributes<HTMLDivElement> { channel: string; visitors: number; conversions: number; trend: "up" | "down" | "flat"; }
const ChannelCard = React.forwardRef<HTMLDivElement, ChannelCardProps>(({ className, channel, visitors, conversions, trend, ...props }, ref) => (
  <div ref={ref} className={cn("flex items-center justify-between rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] px-[var(--spacing-lg)] py-[var(--spacing-md)]", className)} {...props}>
    <span className="text-[var(--font-sm)] font-medium text-[var(--text-primary)]">{channel}</span>
    <div className="flex items-center gap-[var(--spacing-lg)] text-[var(--font-xs)]"><span className="font-mono text-[var(--text-secondary)]">{visitors.toLocaleString()} visits</span><span className="font-mono text-[var(--text-secondary)]">{conversions} conv</span><span className={cn("font-bold", trend === "up" ? "text-[var(--status-healthy)]" : trend === "down" ? "text-[var(--status-error)]" : "text-[var(--text-muted)]")}>{trend === "up" ? "\u2191" : trend === "down" ? "\u2193" : "\u2192"}</span></div>
  </div>
));
ChannelCard.displayName = "ChannelCard";
export { ChannelCard };
