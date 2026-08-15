"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface LogViewerProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const LogViewer = React.forwardRef<HTMLDivElement, LogViewerProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(-RadiusLg)] border border-[var(-BorderDefault)] bg-[var(-SurfaceCard)] p-[var(-SpacingLg)]", className)} {...props}>
    <div className="text-[var(-FontSm)] fontSemibold text-[var(-TextPrimary)]">Log Viewer</div>
    <p className="mt-[var(-SpacingXs)] text-[var(-FontXs)] text-[var(-TextMuted)]">Structured log stream viewer</p>
    <div className="mt-[var(-SpacingSm)] text-[var(-FontXs)] text-[var(-TextSecondary)]">{label || "Ready"}</div>
  </div>
));
LogViewer.displayName = "LogViewer";
export { LogViewer };
