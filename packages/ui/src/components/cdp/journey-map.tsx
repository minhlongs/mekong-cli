"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface JourneyMapProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const JourneyMap = React.forwardRef<HTMLDivElement, JourneyMapProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Journey Map</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Customer journey stage visualization</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
JourneyMap.displayName = "JourneyMap";
export { JourneyMap };
