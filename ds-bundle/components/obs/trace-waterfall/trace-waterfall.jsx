// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/obs/trace-waterfall.tsx
// Bundled in _ds_bundle.js as window.TraceWaterfall

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface TraceWaterfallProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const TraceWaterfall = React.forwardRef<HTMLDivElement, TraceWaterfallProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Trace Waterfall</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Distributed trace timeline visualization</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
TraceWaterfall.displayName = "TraceWaterfall";
export { TraceWaterfall };
