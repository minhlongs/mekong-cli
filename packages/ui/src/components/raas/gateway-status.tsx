"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface GatewayStatusProps extends React.HTMLAttributes<HTMLDivElement> { routes: number; latencyMs: number; uptime: number; }
const GatewayStatus = React.forwardRef<HTMLDivElement, GatewayStatusProps>(({ className, routes, latencyMs, uptime, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="mb-[var(-SpacingSm)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">API Gateway</div>
    <div className="grid gridCols3 gap-[var(-SpacingMd)]">
      <div className="flex flexCol"><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Routes</span><span className="fontMono text-[var(-FontLg)] text-[var(-TextPrimary)]">{routes}</span></div>
      <div className="flex flexCol"><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">P50 Latency</span><span className="fontMono text-[var(-FontLg)] text-[var(-TextPrimary)]">{latencyMs}ms</span></div>
      <div className="flex flexCol"><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Uptime</span><span className={cn("fontMono text-[var(-FontLg)]", uptime > 99.9 ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusWarning)]")}>{uptime}%</span></div>
    </div>
  </div>
));
GatewayStatus.displayName = "GatewayStatus";
export { GatewayStatus };
