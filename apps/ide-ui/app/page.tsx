import { HeroSection } from "@/components/hero-section";
import { FeatureGrid } from "@/components/feature-grid";
import { PricingSection } from "@/components/pricing-section";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex flex-col items-center">
      {/* Nav */}
      <nav
        className="w-full px-6 py-4 flex items-center justify-between border-b border-[var(--md-sys-color-outline)]"
        style={{ background: "var(--md-sys-color-surface)" }}
      >
        <span
          className="m3-title-medium"
          style={{ color: "var(--md-sys-color-primary)" }}
        >
          Mekong IDE
        </span>
        <a
          href="https://github.com/longtho638-jpg/mekong-cli"
          target="_blank"
          rel="noreferrer"
          className="m3-label-large transition-opacity hover:opacity-70"
          style={{ color: "var(--md-sys-color-on-surface-variant)" }}
        >
          GitHub
        </a>
      </nav>

      {/* Hero */}
      <HeroSection />

      {/* Divider */}
      <hr
        className="w-full max-w-5xl border-[var(--md-sys-color-outline)]"
      />

      {/* Features */}
      <FeatureGrid />

      {/* Divider */}
      <hr
        className="w-full max-w-5xl border-[var(--md-sys-color-outline)]"
      />

      {/* Pricing */}
      <PricingSection />

      {/* Footer */}
      <footer
        className="w-full px-6 py-8 text-center border-t border-[var(--md-sys-color-outline)] m3-body-medium"
        style={{ color: "var(--md-sys-color-on-surface-variant)" }}
      >
        © 2026 Mekong IDE — MIT License —{" "}
        <a
          href="https://www.mekongmind.com"
          className="hover:underline"
          style={{ color: "var(--md-sys-color-primary)" }}
        >
          mekongmind.com
        </a>
      </footer>
    </main>
  );
}
