import { MD3Button } from "./md3-button";
import { MD3Card } from "./md3-card";

interface Plan {
  name: string;
  price: string;
  credits: string;
  url: string;
  highlighted: boolean;
}

const PLANS: Plan[] = [
  {
    name: "Starter",
    price: "$49/mo",
    credits: "200 credits",
    url: "https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA",
    highlighted: false,
  },
  {
    name: "Growth",
    price: "$149/mo",
    credits: "1,000 credits",
    url: "https://buy.polar.sh/polar_cl_TDhelBvQfsZq3Rayqf9to4tl0UD6D04OBFqXm1zJDVC",
    highlighted: true,
  },
  {
    name: "Pro",
    price: "$499/mo",
    credits: "5,000 credits",
    url: "https://buy.polar.sh/polar_cl_zi7LHdaPk93V0xbNVQZgqum96gWCFDTVzpDNR2kfN3j",
    highlighted: false,
  },
];

export function PricingSection() {
  return (
    <section className="px-6 py-16 max-w-4xl mx-auto w-full">
      <h2
        className="m3-headline-medium text-center mb-4"
        style={{ color: "var(--md-sys-color-on-background)" }}
      >
        Simple Pricing
      </h2>
      <p
        className="m3-body-large text-center mb-12"
        style={{ color: "var(--md-sys-color-on-surface-variant)" }}
      >
        1 MCU = 1 credit. Deducted only on successful delivery.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => (
          <MD3Card
            key={plan.name}
            variant={plan.highlighted ? "filled" : "outlined"}
            className="flex flex-col gap-5"
          >
            {plan.highlighted && (
              <span
                className="m3-label-medium self-start px-3 py-1 rounded-[var(--md-sys-shape-corner-full)]"
                style={{
                  background: "var(--md-sys-color-primary-container)",
                  color: "var(--md-sys-color-on-primary-container)",
                }}
              >
                Most Popular
              </span>
            )}
            <div>
              <p
                className="m3-title-medium"
                style={{ color: "var(--md-sys-color-on-surface)" }}
              >
                {plan.name}
              </p>
              <p
                className="m3-headline-small mt-1"
                style={{ color: "var(--md-sys-color-primary)" }}
              >
                {plan.price}
              </p>
              <p
                className="m3-body-medium mt-1"
                style={{ color: "var(--md-sys-color-on-surface-variant)" }}
              >
                {plan.credits}
              </p>
            </div>
            <MD3Button
              href={plan.url}
              target="_blank"
              rel="noreferrer"
              variant={plan.highlighted ? "filled" : "outlined"}
            >
              Get {plan.name}
            </MD3Button>
          </MD3Card>
        ))}
      </div>
    </section>
  );
}
