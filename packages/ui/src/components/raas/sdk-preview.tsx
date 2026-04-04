"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface SdkPreviewProps extends React.HTMLAttributes<HTMLDivElement> { language: string; code: string; endpoint: string; }
const SdkPreview = React.forwardRef<HTMLDivElement, SdkPreviewProps>(({ className, language, code, endpoint, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] overflow-hidden", className)} {...props}>
    <div className="flex items-center justify-between border-b border-[var(--border-default)] px-[var(--spacing-lg)] py-[var(--spacing-sm)]">
      <span className="text-[var(--font-xs)] font-semibold text-[var(--text-primary)] uppercase">{language}</span>
      <span className="font-mono text-[var(--font-xs)] text-[var(--text-muted)]">{endpoint}</span>
    </div>
    <pre className="p-[var(--spacing-lg)] font-mono text-[var(--font-xs)] text-[var(--accent-teal-400)] overflow-x-auto">{code}</pre>
  </div>
));
SdkPreview.displayName = "SdkPreview";
export { SdkPreview };
