"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const MetricCard = React.forwardRef<HTMLDivElement, MetricCardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Metric Card</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Single metric with sparkline and threshold</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
MetricCard.displayName = "MetricCard";
export { MetricCard };
