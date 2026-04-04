"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Segment-builderProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Segment-builder = React.forwardRef<HTMLDivElement, Segment-builderProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Segment Builder</div>
    <p className="mt-[var(--spacing-xs)] text-[var(--font-xs)] text-[var(--text-muted)]">Dynamic segment criteria builder</p>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-secondary)]">{label || "Ready"}</div>
  </div>
));
Segment-builder.displayName = "Segment-builder";
export { Segment-builder };
