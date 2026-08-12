// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/marketing/trust-bar.tsx
// Bundled in _ds_bundle.js as window.TrustBar

"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface TrustBarProps extends React.HTMLAttributes<HTMLDivElement> {
  githubStars?: number;
  npmDownloads?: number;
  license?: string;
}

const TrustBar = React.forwardRef<HTMLDivElement, TrustBarProps>(
  ({ className, githubStars, npmDownloads, license = "MIT", ...props }, ref) => (
    <div
      className={cn(
        "flex flexWrap itemsCenter justifyCenter gap-[var(-Spacing6)] py-[var(-Spacing4)]",
        className
      )}
      ref={ref}
      {...props}
    >
      {githubStars !== undefined && (
        <span className="flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l3.046 2.97.719 4.192a.75.75 0 0 11.088.791L8 12.347l3.766 1.98a.75.75 0 0 11.088-.79l.724.194L.818 6.374a.75.75 0 0 1 .4161.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>
          {githubStars.toLocaleString()} stars
        </span>
      )}
      {npmDownloads !== undefined && (
        <span className="flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
          {npmDownloads.toLocaleString()} downloads
        </span>
      )}
      <span className="flex itemsCenter gap1.5 rounded-[var(-RadiusFull)] border border-[var(-BorderDefault)] bg-[var(-BgSecondary)] px3 py1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
        {license} Licensed
      </span>
    </div>
  )
);
TrustBar.displayName = "TrustBar";

export { TrustBar };
