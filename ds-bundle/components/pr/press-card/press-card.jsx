// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pr/press-card.tsx
// Bundled in _ds_bundle.js as window.PressCard

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface PressCardProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const PressCard = React.forwardRef<HTMLDivElement, PressCardProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Press</div>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{label || "Component ready"}</div>
  </div>
));
PressCard.displayName = "PressCard";
export { PressCard };
