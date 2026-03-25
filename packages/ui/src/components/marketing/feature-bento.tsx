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
        "grid auto-rows-[minmax(180px,auto)] grid-cols-1 gap-[var(--spacing-4)] md:grid-cols-3",
        className
      )}
      ref={ref}
      {...props}
    >
      {items.map((item, i) => (
        <div
          key={i}
          className={cn(
            "group flex flex-col gap-[var(--spacing-4)] overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--bg-primary)] p-[var(--spacing-6)] transition-shadow duration-[var(--duration-normal)] hover:shadow-[var(--shadow-md)]",
            item.span === "2" && "md:col-span-2"
          )}
        >
          {item.icon && (
            <span className="text-[var(--accent)]">{item.icon}</span>
          )}
          <h3 className="text-[var(--font-size-lg)] font-semibold text-[var(--text-primary)]">
            {item.title}
          </h3>
          <p className="text-[var(--font-size-sm)] text-[var(--text-secondary)] leading-relaxed">
            {item.description}
          </p>
          {item.demo && (
            <div className="mt-auto">{item.demo}</div>
          )}
        </div>
      ))}
    </div>
  )
);
FeatureBento.displayName = "FeatureBento";

export { FeatureBento };
