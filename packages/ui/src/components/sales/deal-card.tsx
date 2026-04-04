"use client";
import * as React from "react";
import { cn } from "../../lib/utils";
export interface DealCardProps extends React.HTMLAttributes<HTMLDivElement> { company: string; value: number; stage: string; probability: number; owner: string; }
const DealCard = React.forwardRef<HTMLDivElement, DealCardProps>(({ className, company, value, stage, probability, owner, ...props }, ref) => (
  <div ref={ref} className={cn("flex flex-col gap-[var(--spacing-sm)] rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-card)] p-[var(--spacing-lg)]", className)} {...props}>
    <div className="flex items-center justify-between"><span className="text-[var(--font-sm)] font-semibold text-[var(--text-primary)]">{company}</span><span className="font-mono text-[var(--font-sm)] text-[var(--accent-teal-400)]">${(value / 1000).toFixed(0)}K</span></div>
    <div className="flex items-center justify-between text-[var(--font-xs)]"><span className="rounded-[var(--radius-sm)] bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[var(--text-muted)]">{stage}</span><span className="text-[var(--text-secondary)]">{probability}%</span><span className="text-[var(--text-muted)]">{owner}</span></div>
  </div>
));
DealCard.displayName = "DealCard";
export { DealCard };
