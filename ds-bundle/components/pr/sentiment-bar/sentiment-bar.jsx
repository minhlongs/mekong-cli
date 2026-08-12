// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/pr/sentiment-bar.tsx
// Bundled in _ds_bundle.js as window.SentimentBar

"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface SentimentBarProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const SentimentBar = React.forwardRef<HTMLDivElement, SentimentBarProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Sentiment</div>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextMuted)]">{label || "Component ready"}</div>
  </div>
));
SentimentBar.displayName = "SentimentBar";
export { SentimentBar };
