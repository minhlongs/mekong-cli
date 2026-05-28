"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const policyStatusVariants = cva(
  "inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium",
  {
    variants: {
      status: {
        active: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
        draft: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
        expired: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      },
    },
    defaultVariants: { status: "active" },
  }
);

export interface Policy {
  name: string;
  status: "active" | "draft" | "expired";
  lastReview: string;
}

export interface PolicyStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  policies: Policy[];
}

const PolicyStatus = React.forwardRef<HTMLDivElement, PolicyStatusProps>(
  ({ className, policies, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "flex flexCol rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden",
        className
      )}
      {...props}
    >
      <div className="borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]">
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">
          Policy Compliance
        </span>
      </div>
      <div className="flex flexCol">
        {policies.map((policy, i) => (
          <div
            key={i}
            className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingMd)] last:borderB0 hover:bg-[var(-SurfaceHover)]"
          >
            <span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">
              {policy.name}
            </span>
            <div className="flex itemsCenter gap-[var(-SpacingMd)]">
              <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">
                {policy.lastReview}
              </span>
              <span className={policyStatusVariants({ status: policy.status })}>
                {policy.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
);
PolicyStatus.displayName = "PolicyStatus";

export { PolicyStatus, policyStatusVariants };
