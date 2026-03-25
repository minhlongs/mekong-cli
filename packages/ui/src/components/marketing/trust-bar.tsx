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
        "flex flex-wrap items-center justify-center gap-[var(--spacing-6)] py-[var(--spacing-4)]",
        className
      )}
      ref={ref}
      {...props}
    >
      {githubStars !== undefined && (
        <span className="flex items-center gap-1.5 rounded-[var(--radius-full)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-1 text-[var(--font-size-sm)] text-[var(--text-secondary)]">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>
          {githubStars.toLocaleString()} stars
        </span>
      )}
      {npmDownloads !== undefined && (
        <span className="flex items-center gap-1.5 rounded-[var(--radius-full)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-1 text-[var(--font-size-sm)] text-[var(--text-secondary)]">
          {npmDownloads.toLocaleString()} downloads
        </span>
      )}
      <span className="flex items-center gap-1.5 rounded-[var(--radius-full)] border border-[var(--border-default)] bg-[var(--bg-secondary)] px-3 py-1 text-[var(--font-size-sm)] text-[var(--text-secondary)]">
        {license} Licensed
      </span>
    </div>
  )
);
TrustBar.displayName = "TrustBar";

export { TrustBar };
