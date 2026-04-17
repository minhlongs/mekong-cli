import { Zap } from "lucide-react";
import { MD3Button } from "./md3-button";

const POLAR_STARTER_URL =
  "https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA";

export function HeroSection() {
  return (
    <section className="flex flex-col items-center justify-center text-center px-6 py-20 md:py-32">
      {/* Badge */}
      <div
        className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-[var(--md-sys-shape-corner-full)] border border-[var(--md-sys-color-outline)] m3-label-medium"
        style={{ color: "var(--md-sys-color-primary)" }}
      >
        <Zap size={14} />
        <span>One person. 10 business layers. $49/mo.</span>
      </div>

      {/* Headline */}
      <h1
        className="m3-display-large max-w-3xl mb-6"
        style={{ color: "var(--md-sys-color-on-background)" }}
      >
        The{" "}
        <span style={{ color: "var(--md-sys-color-primary)" }}>
          One-Person Company
        </span>{" "}
        Platform
      </h1>

      {/* Sub-headline */}
      <p
        className="m3-body-large max-w-xl mb-10"
        style={{ color: "var(--md-sys-color-on-surface-variant)" }}
      >
        Replace a 50-person team with autonomous agents. 443 command definitions
        across 10 business layers — Founder, Business, Product, Engineering, Ops
        and more.
      </p>

      {/* CTA row */}
      <div className="flex flex-col sm:flex-row gap-4">
        <MD3Button href={POLAR_STARTER_URL} target="_blank" rel="noreferrer">
          Start for $49/mo
        </MD3Button>
        <MD3Button
          variant="outlined"
          href="/departments/engineering"
        >
          See Engineering Layer
        </MD3Button>
      </div>

      {/* Social proof */}
      <p
        className="mt-8 m3-label-medium"
        style={{ color: "var(--md-sys-color-on-surface-variant)" }}
      >
        MIT · Self-hosted · Your data never leaves your machine
      </p>
    </section>
  );
}
