"use client";

import * as React from "react";
import { cn } from "../../lib/utils";

export interface HeroSectionProps extends React.HTMLAttributes<HTMLElement> {
  title: string;
  subtitle: string;
  primaryCta?: { label: string; href: string };
  secondaryCta?: { label: string; href: string };
  terminal?: React.ReactNode;
}

const HeroSection = React.forwardRef<HTMLElement, HeroSectionProps>(
  ({ className, title, subtitle, primaryCta, secondaryCta, terminal, ...props }, ref) => (
    <section
      className={cn(
        "flex min-h-[80vh] flex-col items-center justify-center gap-[var(--spacing-8)] px-[var(--spacing-6)] py-[var(--spacing-24)] text-center",
        className
      )}
      ref={ref}
      {...props}
    >
      <div className="flex max-w-3xl flex-col items-center gap-[var(--spacing-6)]">
        <h1 className="text-[var(--font-size-hero)] font-bold leading-[1.1] tracking-tight text-[var(--text-primary)]">
          {title}
        </h1>
        <p className="max-w-xl text-[var(--font-size-lg)] text-[var(--text-secondary)] leading-relaxed">
          {subtitle}
        </p>
        <div className="flex items-center gap-[var(--spacing-4)]">
          {primaryCta && (
            <a
              href={primaryCta.href}
              className="inline-flex h-12 items-center rounded-[var(--radius-lg)] bg-[var(--accent)] px-8 text-[var(--font-size-base)] font-semibold text-[var(--accent-text)] transition-colors duration-[var(--duration-normal)] hover:bg-[var(--accent-hover)]"
            >
              {primaryCta.label}
            </a>
          )}
          {secondaryCta && (
            <a
              href={secondaryCta.href}
              className="inline-flex h-12 items-center rounded-[var(--radius-lg)] border border-[var(--border-strong)] px-8 text-[var(--font-size-base)] font-semibold text-[var(--text-primary)] transition-colors duration-[var(--duration-normal)] hover:bg-[var(--bg-tertiary)]"
            >
              {secondaryCta.label}
            </a>
          )}
        </div>
      </div>
      {terminal && <div className="w-full max-w-2xl">{terminal}</div>}
    </section>
  )
);
HeroSection.displayName = "HeroSection";

export { HeroSection };
