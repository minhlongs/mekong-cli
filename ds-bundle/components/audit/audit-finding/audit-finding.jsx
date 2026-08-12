// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/audit/audit-finding.tsx
// Bundled in _ds_bundle.js as window.AuditFinding

"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const findingSeverity = cva("inlineFlex itemsCenter rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontBold uppercase", {
  variants: {
    severity: {
      "materialWeakness": "bg-[var(-StatusError)]/20 text-[var(-StatusError)]",
      "significantDeficiency": "bg-[var(-StatusWarning)]/20 text-[var(-StatusWarning)]",
      "deficiency": "bg-[var(-StatusIdle)]/20 text-[var(-TextSecondary)]",
    },
  },
  defaultVariants: { severity: "deficiency" },
});

export interface AuditFindingProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  severity: "materialWeakness" | "significantDeficiency" | "deficiency";
  owner: string;
  dueDate: string;
  description: string;
}

const AuditFinding = React.forwardRef<HTMLDivElement, AuditFindingProps>(
  ({ className, title, severity, owner, dueDate, description, ...props }, ref) => (
    <div ref={ref} className={cn("flex flexCol gap-[var(-SpacingSm)] rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
      <div className="flex itemsCenter justifyBetween">
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">{title}</span>
        <span className={findingSeverity({ severity })}>{severity.replace("-", " ")}</span>
      </div>
      <p className="text-[var(-FontSm)] text-[var(-TextSecondary)]">{description}</p>
      <div className="flex itemsCenter justifyBetween borderT border-[var(-BorderDefault)] pt-[var(-SpacingSm)]">
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Owner: {owner}</span>
        <span className="text-[var(-FontXs)] text-[var(-TextMuted)]">Due: {dueDate}</span>
      </div>
    </div>
  )
);
AuditFinding.displayName = "AuditFinding";
export { AuditFinding, findingSeverity };
