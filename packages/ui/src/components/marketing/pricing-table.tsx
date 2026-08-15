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

export interface PricingTableProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'> {
  tiers: PricingTier[];
  onSelect?: (tier: PricingTier) => void;
}

const PricingTable = React.forwardRef<HTMLDivElement, PricingTableProps>(
  ({ className, tiers, onSelect, ...props }, ref) => (
    <div
      className={cn(
        "grid gridCols1 gap-[var(-Spacing6)] md:gridCols2 lg:gridCols4",
        className
      )}
      ref={ref}
      {...props}
    >
      {tiers.map((tier) => (
        <div
          key={tier.name}
          className={cn(
            "flex flexCol rounded-[var(-RadiusXl)] border p-[var(-Spacing6)]",
            tier.highlighted
              ? "border-[var(-Accent)] bg-[var(-Accent)]/5 ring1 ring-[var(-Accent)]"
              : "border-[var(-BorderDefault)] bg-[var(-BgPrimary)]"
          )}
        >
          <h3 className="text-[var(-FontSizeLg)] fontSemibold text-[var(-TextPrimary)]">{tier.name}</h3>
          <div className="mt-[var(-Spacing4)]">
            <span className="fontMono text-[var(-FontSize4xl)] fontBold text-[var(-TextPrimary)]">
              {typeof tier.price === "number" ? `$${tier.price}` : tier.price}
            </span>
            {typeof tier.price === "number" && (
              <span className="text-[var(-FontSizeSm)] text-[var(-TextTertiary)]">/mo</span>
            )}
          </div>
          <p className="mt1 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
            {typeof tier.credits === "number" ? `${tier.credits.toLocaleString()} credits` : tier.credits}
          </p>
          <ul className="mt-[var(-Spacing6)] flex flex1 flexCol gap-[var(-Spacing2)]">
            {tier.features.map((feature) => (
              <li key={feature} className="flex itemsStart gap2 text-[var(-FontSizeSm)] text-[var(-TextSecondary)]">
                <span className="mt0.5 text-[var(-ColorSuccess500)]">&#x2713;</span>
                {feature}
              </li>
            ))}
          </ul>
          <button
            onClick={() => onSelect?.(tier)}
            className={cn(
              "mt-[var(-Spacing6)] inlineFlex h10 itemsCenter justifyCenter rounded-[var(-RadiusMd)] px4 text-[var(-FontSizeSm)] fontSemibold transitionColors duration-[var(-DurationNormal)]",
              tier.highlighted
                ? "bg-[var(-Accent)] text-[var(-AccentText)] hover:bg-[var(-AccentHover)]"
                : "border border-[var(-BorderStrong)] text-[var(-TextPrimary)] hover:bg-[var(-BgTertiary)]"
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
