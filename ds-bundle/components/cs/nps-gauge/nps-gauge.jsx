// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/cs/nps-gauge.tsx
// Bundled in _ds_bundle.js as window.NpsGauge

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface NpsGaugeProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const NpsGauge = React.forwardRef<HTMLDivElement, NpsGaugeProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">NPS</div>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{label || "Component ready"}</div>
  </div>
));
NpsGauge.displayName = "NpsGauge";
export { NpsGauge };
