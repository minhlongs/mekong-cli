"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils";

const vulnSeverityVariants = cva(
  "inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontBold uppercase trackingWider",
  {
    variants: {
      severity: {
        critical: "bg-[var(-StatusError)]/20 text-[var(-StatusError)]",
        high: "bg-[var(-StatusWarning)]/20 text-[var(-StatusWarning)]",
        medium: "bg-[var(-AccentTeal500)]/20 text-[var(-AccentTeal400)]",
        low: "bg-[var(-StatusIdle)]/20 text-[var(-StatusIdle)]",
      },
    },
    defaultVariants: { severity: "medium" },
  }
);

export interface VulnCardProps extends React.HTMLAttributes<HTMLDivElement> {
  cve: string;
  severity: "critical" | "high" | "medium" | "low";
  component: string;
  slaHours: number;
  status: string;
}

const VulnCard = React.forwardRef<HTMLDivElement, VulnCardProps>(
  ({ className, cve, severity, component, slaHours, status, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]",
        className
      )}
      {...props}
    >
      <div className="flex itemsCenter justifyBetween">
        <span className="fontMono text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">
          {cve}
        </span>
        <span className={vulnSeverityVariants({ severity })}>{severity}</span>
      </div>
      <span className="text-[var(-FontSm)] text-[var(-TextSecondary)]">
        {component}
      </span>
      <div className="flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]">
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">
          SLA: {slaHours}h
        </span>
        <span className="text-[var(-FontXs)] fontMedium text-[var(-TextSecondary)]">
          {status}
        </span>
      </div>
    </div>
  )
);
VulnCard.displayName = "VulnCard";

export { VulnCard, vulnSeverityVariants };
