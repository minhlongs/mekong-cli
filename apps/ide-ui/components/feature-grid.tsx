import { Code2, Building2, ShieldCheck } from "lucide-react";
import { MD3Card } from "./md3-card";

interface Feature {
  icon: React.ReactNode;
  title: string;
  body: string;
}

const FEATURES: Feature[] = [
  {
    icon: <Code2 size={24} style={{ color: "var(--md-sys-color-primary)" }} />,
    title: "Engineering Layer",
    body: "66 commands — cook, code, review, deploy, test. Agents write, test, and ship code autonomously.",
  },
  {
    icon: (
      <Building2 size={24} style={{ color: "var(--md-sys-color-primary)" }} />
    ),
    title: "Business Layer",
    body: "71 commands — sales, marketing, finance, HR. Run revenue operations without hiring a single employee.",
  },
  {
    icon: (
      <ShieldCheck
        size={24}
        style={{ color: "var(--md-sys-color-primary)" }}
      />
    ),
    title: "Ops Layer",
    body: "41 commands — audit, health, security, status. Continuous monitoring and quality gates 24/7.",
  },
];

export function FeatureGrid() {
  return (
    <section className="px-6 py-16 max-w-5xl mx-auto w-full">
      <h2
        className="m3-headline-medium text-center mb-12"
        style={{ color: "var(--md-sys-color-on-background)" }}
      >
        10 Business Layers. One Subscription.
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {FEATURES.map((f) => (
          <MD3Card key={f.title} variant="elevated" className="flex flex-col gap-4">
            <div
              className="w-10 h-10 flex items-center justify-center rounded-[var(--md-sys-shape-corner-small)]"
              style={{
                background: "var(--md-sys-color-primary-container)",
              }}
            >
              {f.icon}
            </div>
            <h3
              className="m3-title-medium"
              style={{ color: "var(--md-sys-color-on-surface)" }}
            >
              {f.title}
            </h3>
            <p
              className="m3-body-medium"
              style={{ color: "var(--md-sys-color-on-surface-variant)" }}
            >
              {f.body}
            </p>
          </MD3Card>
        ))}
      </div>
    </section>
  );
}
