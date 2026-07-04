"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface EvalResult { name: string; passed: boolean; score: number; baseline: number; }
export interface EvalSuiteProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'results'> { results: EvalResult[]; }

const EvalSuite = React.forwardRef<HTMLDivElement, EvalSuiteProps>(
  ({ className, results, ...props }, ref) => {
    const passCount = results.filter((r) => r.passed).length;
    return (
      <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className)} {...props}>
        <div className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]">
          <span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Eval Suite</span>
          <span className="fontMono text-[var(-FontXs)] text-[var(-TextMuted)]">{passCount}/{results.length} passed</span>
        </div>
        {results.map((r, i) => (
          <div key={i} className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)] last:borderB0 hover:bg-[var(-SurfaceHover)]">
            <div className="flex itemsCenter gap-[var(-SpacingSm)]">
              <span className={cn("fontBold", r.passed ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusError)]")}>{r.passed ? "\u2713" : "\u2717"}</span>
              <span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">{r.name}</span>
            </div>
            <div className="flex itemsCenter gap-[var(-SpacingMd)] fontMono text-[var(-FontXs)]">
              <span className="text-[var(-TextMuted)]">baseline: {r.baseline.toFixed(2)}</span>
              <span className={cn(r.score >= r.baseline ? "text-[var(-StatusHealthy)]" : "text-[var(-StatusError)]")}>{r.score.toFixed(2)}</span>
            </div>
          </div>
        ))}
      </div>
    );
  }
);
EvalSuite.displayName = "EvalSuite";
export { EvalSuite };
