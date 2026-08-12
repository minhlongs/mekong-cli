// Source excerpt: /Users/macbook/mekong-cli/packages/ui/src/components/marketing/hero-section.tsx
// Bundled in _ds_bundle.js as window.HeroSection

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
        "flex minH-[80vh] flexCol itemsCenter justifyCenter gap-[var(-Spacing8)] px-[var(-Spacing6)] py-[var(-Spacing24)] textCenter",
        className
      )}
      ref={ref}
      {...props}
    >
      <div className="flex maxW3xl flexCol itemsCenter gap-[var(-Spacing6)]">
        <h1 className="text-[var(-FontSizeHero)] fontBold leading-[1.1] trackingTight text-[var(-TextPrimary)]">
          {title}
        </h1>
        <p className="maxWXl text-[var(-FontSizeLg)] text-[var(-TextSecondary)] leadingRelaxed">
          {subtitle}
        </p>
        <div className="flex itemsCenter gap-[var(-Spacing4)]">
          {primaryCta && (
            <a
              href={primaryCta.href}
              className="inlineFlex h12 itemsCenter rounded-[var(-RadiusLg)] bg-[var(-Accent)] px8 text-[var(-FontSizeBase)] fontSemibold text-[var(-AccentText)] transitionColors duration-[var(-DurationNormal)] hover:bg-[var(-AccentHover)]"
            >
              {primaryCta.label}
            </a>
          )}
          {secondaryCta && (
            <a
              href={secondaryCta.href}
              className="inlineFlex h12 itemsCenter rounded-[var(-RadiusLg)] border border-[var(-BorderStrong)] px8 text-[var(-FontSizeBase)] fontSemibold text-[var(-TextPrimary)] transitionColors duration-[var(-DurationNormal)] hover:bg-[var(-BgTertiary)]"
            >
              {secondaryCta.label}
            </a>
          )}
        </div>
      </div>
      {terminal && <div className="wFull maxW2xl">{terminal}</div>}
    </section>
  )
);
HeroSection.displayName = "HeroSection";

export { HeroSection };
