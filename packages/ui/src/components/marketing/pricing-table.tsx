"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface PricingTier {
  name: string;
  price: number | string;
  credits: number | string;
  features: string[];
  cta: string;
  highlighted?: boolean;
}

export interface PricingTableProps extends React.HTMLAttributes<HTMLDivElement> {
  tiers: PricingTier[];
  onSelect?: (tier: PricingTier) => void;
}

const PricingTable = React.forwardRef<HTMLDivElement, PricingTableProps>(
  ({ className, tiers, onSelect, ...props }, ref) => (
    <div
      className={cn(
        "grid grid-cols-1 gap-[var(--spacing-6)] md:grid-cols-2 lg:grid-cols-4",
        className
      )}
      ref={ref}
      {...props}
    >
      {tiers.map((tier) => (
        <div
          key={tier.name}
          className={cn(
            "flex flex-col rounded-[var(--radius-xl)] border p-[var(--spacing-6)]",
            tier.highlighted
              ? "border-[var(--accent)] bg-[var(--accent)]/5 ring-1 ring-[var(--accent)]"
              : "border-[var(--border-default)] bg-[var(--bg-primary)]"
          )}
        >
          <h3 className="text-[var(--font-size-lg)] font-semibold text-[var(--text-primary)]">{tier.name}</h3>
          <div className="mt-[var(--spacing-4)]">
            <span className="font-mono text-[var(--font-size-4xl)] font-bold text-[var(--text-primary)]">
              {typeof tier.price === "number" ? `$${tier.price}` : tier.price}
            </span>
            {typeof tier.price === "number" && (
              <span className="text-[var(--font-size-sm)] text-[var(--text-tertiary)]">/mo</span>
            )}
          </div>
          <p className="mt-1 text-[var(--font-size-sm)] text-[var(--text-secondary)]">
            {typeof tier.credits === "number" ? `${tier.credits.toLocaleString()} credits` : tier.credits}
          </p>
          <ul className="mt-[var(--spacing-6)] flex flex-1 flex-col gap-[var(--spacing-2)]">
            {tier.features.map((feature) => (
              <li key={feature} className="flex items-start gap-2 text-[var(--font-size-sm)] text-[var(--text-secondary)]">
                <span className="mt-0.5 text-[var(--color-success-500)]">&#x2713;</span>
                {feature}
              </li>
            ))}
          </ul>
          <button
            onClick={() => onSelect?.(tier)}
            className={cn(
              "mt-[var(--spacing-6)] inline-flex h-10 items-center justify-center rounded-[var(--radius-md)] px-4 text-[var(--font-size-sm)] font-semibold transition-colors duration-[var(--duration-normal)]",
              tier.highlighted
                ? "bg-[var(--accent)] text-[var(--accent-text)] hover:bg-[var(--accent-hover)]"
                : "border border-[var(--border-strong)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]"
            )}
          >
            {tier.cta}
          </button>
        </div>
      ))}
    </div>
  )
);
PricingTable.displayName = "PricingTable";

export { PricingTable };
