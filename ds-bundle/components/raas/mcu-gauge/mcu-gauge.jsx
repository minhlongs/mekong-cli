// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/raas/mcu-gauge.tsx
// Bundled in _ds_bundle.js as window.McuGauge

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface McuGaugeProps extends React.HTMLAttributes<HTMLDivElement> { used: number; total: number; tier: string; }
const McuGauge = React.forwardRef<HTMLDivElement, McuGaugeProps>(({ className, used, total, tier, ...props }, ref) => {
  const pct = Math.round((used / total) * 100);
  return (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="flex itemsCenter justifyBetween mb-[var(-SpacingSm)]"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">MCU Credits</span><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{tier}</span></div>
      <div className="fontMono text-[var(-Font2xl)] fontBold text-[var(-TextPrimary)]">{used}<span className="text-[var(-FontSm)] text-[var(-TextMuted)]">/{total}</span></div>
      <div className="mt-[var(-SpacingSm)] h2 wFull roundedFull bg-[var(-BgTertiary)] overflowHidden"><div className={cn("hFull roundedFull transitionAll", pct > 90 ? "bg-[var(-StatusError)]" : pct > 70 ? "bg-[var(-StatusWarning)]" : "bg-[var(-AccentTeal500)]")} style={{ width: `${pct}%` }} /></div>
    </div>
  );
});
McuGauge.displayName = "McuGauge";
export { McuGauge };
