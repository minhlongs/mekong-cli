// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/audit/control-card.tsx
// Bundled in _ds_bundle.js as window.ControlCard

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const testStatusVariants = cva("inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    status: {
      passed: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
      failed: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      pending: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      "notTested": "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]",
    },
  },
  defaultVariants: { status: "notTested" },
});

export interface ControlCardProps extends React.HTMLAttributes<HTMLDivElement> {
  controlId: string;
  name: string;
  owner: string;
  testStatus: "passed" | "failed" | "pending" | "notTested";
  lastTested?: string;
}

const ControlCard = React.forwardRef<HTMLDivElement, ControlCardProps>(
  ({ className, controlId, name, owner, testStatus, lastTested, ...props }, ref) => (
    <div ref={ref} className={cn("flex itemsCenter justifyBetween rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] px-[var(-SpacingLg)] py-[var(-SpacingMd)]", className)} {...props}>
      <div className="flex flexCol gap-[var(-SpacingXs)]">
        <div className="flex itemsCenter gap-[var(-SpacingSm)]">
          <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">{controlId}</span>
          <span className="text-[var(-FontSm)] fontMedium text-[var(-TextPrimary)]">{name}</span>
        </div>
        <span className="text-[var(-FontXs)] text-[var(-TextSecondary)]">Owner: {owner}</span>
      </div>
      <div className="flex itemsCenter gap-[var(-SpacingMd)]">
        {lastTested && <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{lastTested}</span>}
        <span className={testStatusVariants({ status: testStatus })}>{testStatus}</span>
      </div>
    </div>
  )
);
ControlCard.displayName = "ControlCard";
export { ControlCard, testStatusVariants };
