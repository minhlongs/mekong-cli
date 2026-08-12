// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/obs/alert-rule.tsx
// Bundled in _ds_bundle.js as window.AlertRule

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface AlertRuleProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const AlertRule = React.forwardRef<HTMLDivElement, AlertRuleProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Alert Rule</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Alert rule with condition and routing</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
AlertRule.displayName = "AlertRule";
export { AlertRule };
