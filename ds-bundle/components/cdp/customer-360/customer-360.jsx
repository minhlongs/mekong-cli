// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/cdp/customer-360.tsx
// Bundled in _ds_bundle.js as window.Customer360

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Customer360Props extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Customer360 = React.forwardRef<HTMLDivElement, Customer360Props>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Customer 360</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Unified customer profile view</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
Customer360.displayName = "Customer360";
export { Customer360 };
