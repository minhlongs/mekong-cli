"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const statusBadge = cva("rounded-[var(-RadiusSm)] px2 py0.5 text-[var(-FontXs)] fontMedium", {
  variants: { status: { filed: "bg-[var(-StatusHealthy)]/15 text-[var(-StatusHealthy)]", drafting: "bg-[var(-StatusWarning)]/15 text-[var(-StatusWarning)]", "notStarted": "bg-[var(-StatusIdle)]/15 text-[var(-StatusIdle)]" } },
  defaultVariants: { status: "notStarted" },
});
export interface Filing { name: string; status: "filed" | "drafting" | "notStarted"; deadline: string; }
export interface FilingStatusProps extends React.HTMLAttributes<HTMLDivElement> { filings: Filing[]; }
const FilingStatus = React.forwardRef<HTMLDivElement, FilingStatusProps>(({ className, filings, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] overflowHidden", className)} {...props}>
    <div className="borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingSm)]"><span className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">SEC Filings</span></div>
    {filings.map((f, i) => (<div key={i} className="flex itemsCenter justifyBetween borderB border-[var(-BorderDefault)] px-[var(-SpacingLg)] py-[var(-SpacingMd)] last:borderB0 hover:bg-[var(-SurfaceHover)]"><span className="text-[var(-FontSm)] text-[var(-TextPrimary)]">{f.name}</span><div className="flex itemsCenter gap-[var(-SpacingMd)]"><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{f.deadline}</span><span className={statusBadge({ status: f.status })}>{f.status}</span></div></div>))}
  </div>
));
FilingStatus.displayName = "FilingStatus";
export { FilingStatus };
