"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface PerfGaugeProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const PerfGauge = React.forwardRef<HTMLDivElement, PerfGaugeProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Performance Gauge</div>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{label || "Component ready"}</div>
  </div>
));
PerfGauge.displayName = "PerfGauge";
export { PerfGauge };
