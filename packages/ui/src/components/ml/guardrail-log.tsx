"use client";

import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";

const triggerBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: {
    action: {
      blocked: "bg-[var(-StatusError)]/15 text-[var(-StatusError)]",
      flagged: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]",
      passed: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]",
    },
  },
  defaultVariants: { action: "passed" },
});

export interface GuardrailEvent { time: string; rule: string; action: "blocked" | "flagged" | "passed"; input: string; }
export interface GuardrailLogProps extends React.HTMLAttributes<HTMLDivElement> { events: GuardrailEvent[]; }

const GuardrailLog = React.forwardRef<HTMLDivElement, GuardrailLogProps>(
  ({ className, events, ...props }, ref) => (
    <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className)} {...props}>
      <div className="borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]">
        <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Guardrail Log</span>
      </div>
      <div className="maxH64 overflowYAuto">
        {events.map((e, i) => (
          <div key={i} className="flex itemsCenter gap-[var(-SpacingMd)] borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0">
            <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)] minW-[48px]">{e.time}</span>
            <span className={triggerBadge({ action: e.action })}>{e.action}</span>
            <span className="text-[var(-FontXs)] text-[var(-TextSecondary)]">{e.rule}</span>
            <span className="flex1 truncate text-[var(-FontXs)] text-[var(-TextMuted)]">{e.input}</span>
          </div>
        ))}
      </div>
    </div>
  )
);
GuardrailLog.displayName = "GuardrailLog";
export { GuardrailLog };
