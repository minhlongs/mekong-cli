"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface Sentiment-barProps extends React.HTMLAttributes<HTMLDivElement> { label?: string; }
const Sentiment-bar = React.forwardRef<HTMLDivElement, Sentiment-barProps>(({ className, label, ...props }, ref) => (
  <div ref={ref} className={cn("rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">Sentiment</div>
    <div className="mt-[var(--spacing-sm)] text-[var(--font-xs)] text-[var(--text-muted)]">{label || "Component ready"}</div>
  </div>
));
Sentiment-bar.displayName = "Sentiment-bar";
export { Sentiment-bar };
