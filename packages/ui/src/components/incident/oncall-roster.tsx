"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface OncallRosterProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const OncallRoster = React.forwardRef<HTMLDivElement, OncallRosterProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">OnCall Roster</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Current onCall rotation and schedule</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
OncallRoster.displayName = "OncallRoster";
export { OncallRoster };
