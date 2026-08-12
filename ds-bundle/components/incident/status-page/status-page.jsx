// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/incident/status-page.tsx
// Bundled in _ds_bundle.js as window.StatusPage

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface StatusPageProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const StatusPage = React.forwardRef<HTMLDivElement, StatusPageProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Status Page</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Service status indicators</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
StatusPage.displayName = "StatusPage";
export { StatusPage };
