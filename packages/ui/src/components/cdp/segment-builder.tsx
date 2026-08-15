"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface SegmentBuilderProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const SegmentBuilder = React.forwardRef<HTMLDivElement, SegmentBuilderProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Segment Builder</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Dynamic segment criteria builder</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
SegmentBuilder.displayName = "SegmentBuilder";
export { SegmentBuilder };
