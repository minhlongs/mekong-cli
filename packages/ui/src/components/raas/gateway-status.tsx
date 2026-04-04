"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface GatewayStatusProps extends React.HTMLAttributes<HTMLDivElement> { routes: number; latencyMs: number; uptime: number; }
const GatewayStatus = React.forwardRef<HTMLDivElement, GatewayStatusProps>(({ className, routes, latencyMs, uptime, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="mb-[var(--spacing-sm)] text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">API Gateway</div>
    <div className="grid grid-cols-3 gap-[var(--spacing-md)]">
      <div className="flex flex-col"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Routes</span><span className="font-mono text-[var(--font-lg)] text-[var(--text-primary)]">{routes}</span></div>
      <div className="flex flex-col"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">P50 Latency</span><span className="font-mono text-[var(--font-lg)] text-[var(--text-primary)]">{latencyMs}ms</span></div>
      <div className="flex flex-col"><span className="text-[var(--font-xs)] text-[var(--text-muted)]">Uptime</span><span className={cn("font-mono text-[var(--font-lg)]", uptime > 99.9 ? "text-[var(--status-healthy)]" : "text-[var(--status-warning)]")}>{uptime}%</span></div>
    </div>
  </div>
));
GatewayStatus.displayName = "GatewayStatus";
export { GatewayStatus };
