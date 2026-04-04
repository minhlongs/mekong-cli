"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Journey-mapProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Journey-map = React.forwardRef<HTMLDivElement, Journey-mapProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Journey Map</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Customer journey stage visualization</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Journey-map.displayName = "Journey-map";
export { Journey-map };
