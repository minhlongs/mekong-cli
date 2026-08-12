// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/ipo/milestone-track.tsx
// Bundled in _ds_bundle.js as window.MilestoneTrack

"use client";
import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "../../lib/utils";
const phaseStatus = cva("flex h8 w8 itemsCenter justifyCenter roundedFull text-[var(-FontXs)] fontBold", {
  variants: { status: { done: "bg-[var(-StatusHealthy)] text-[var(-BgPrimary)]", active: "bg-[var(-AccentTeal500)] text-[var(-BgPrimary)] animatePulse", pending: "bg-[var(-BgTertiary)] text-[var(-TextMuted)]" } },
  defaultVariants: { status: "pending" },
});
export interface Milestone { name: string; date: string; status: "done" | "active" | "pending"; }
export interface MilestoneTrackProps extends React.HTMLAttributes<HTMLDivElement> { milestones: Milestone[]; }
const MilestoneTrack = React.forwardRef<HTMLDivElement, MilestoneTrackProps>(({ className, milestones, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="mb-[var(-SpacingMd)] text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">IPO Milestones</div>
    <div className="flex itemsCenter">{milestones.map((m, i) => (<React.Fragment key={i}><div className="flex flexCol itemsCenter gap-[var(-SpacingXs)]"><span className={phaseStatus({ status: m.status })}>{m.status === "done" ? "\u2713" : i + 1}</span><span className="text-[var(-FontXs)] text-[var(-TextSecondary)] whitespaceNowrap">{m.name}</span><span className="text-[var(-FontXs)] text-[var(-TextMuted)]">{m.date}</span></div>{i < milestones.length - 1 && <div className={cn("h0.5 flex1 mx1 minW-[16px]", m.status === "done" ? "bg-[var(-StatusHealthy)]" : "bg-[var(-BorderDefault)]")} />}</React.Fragment>))}</div>
  </div>
));
MilestoneTrack.displayName = "MilestoneTrack";
export { MilestoneTrack };
