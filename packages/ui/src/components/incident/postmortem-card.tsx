"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface PostmortemCardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const PostmortemCard = React.forwardRef<HTMLDivElement, PostmortemCardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Postmortem Card</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Incident postmortem summary</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
PostmortemCard.displayName = "PostmortemCard";
export { PostmortemCard };
