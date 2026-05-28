"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

interface BentoItem {
  title: string;
  description: string;
  icon?: React.ReactNode;
  demo?: React.ReactNode;
  span?: "1" | "2";
}

export interface FeatureBentoProps extends React.HTMLAttributes<HTMLDivElement> {
  items: BentoItem[];
}

const FeatureBento = React.forwardRef<HTMLDivElement, FeatureBentoProps>(
  ({ className, items, ...props }, ref) => (
    <div
      className={cn(
        "grid autoRows-[minmax(180px,auto)] gridCols1 gap-[var(-Spacing4)] md:gridCols3",
        className
      )}
      ref={ref}
      {...props}
    >
      {items.map((item, i) => (
        <div
          key={i}
          className={cn(
            "group flex flexCol gap-[var(-Spacing4)] overflowHidden rounded-[var(-RadiusXl)] border border-[var(-BorderDefault)] bg-[var(-BgPrimary)] p-[var(-Spacing6)] transitionShadow duration-[var(-DurationNormal)] hover:shadow-[var(-ShadowMd)]",
            item.span === "2" && "md:colSpan2"
          )}
        >
          {item.icon && (
            <span className="text-[var(-Accent)]">{item.icon}</span>
          )}
          <h3 className="text-[var(-FontSizeLg)] fontSemibold text-[var(-TextPrimary)]">
            {item.title}
          </h3>
          <p className="text-[var(-FontSizeSm)] text-[var(-TextSecondary)] leadingRelaxed">
            {item.description}
          </p>
          {item.demo && (
            <div className="mtAuto">{item.demo}</div>
          )}
        </div>
      ))}
    </div>
  )
);
FeatureBento.displayName = "FeatureBento";

export { FeatureBento };
