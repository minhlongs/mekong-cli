import { CheckoutButton } from "./checkout-button";

export function PricingSection() {
  return (
    <section id="pricing" className="py-24 relative overflow-hidden">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
            Simple, Transparent Pricing
          </h2>
          <p className="mt-6 text-lg leading-8 text-slate-600 dark:text-slate-400">
            Start small and scale as you grow. Secure your spot in the ecosystem today.
          </p>
        </div>

        <div className="mx-auto max-w-lg rounded-3xl bg-white dark:bg-slate-900 ring-1 ring-slate-200 dark:ring-slate-800 p-8 xl:p-10 shadow-xl">
          <div className="flex items-center justify-between gap-x-4">
            <h3 className="text-lg font-semibold leading-8 text-slate-900 dark:text-white">Pre-order Access</h3>
            <div className="rounded-full bg-indigo-50 dark:bg-indigo-900/30 px-2.5 py-1 text-xs font-semibold leading-5 text-indigo-600 dark:text-indigo-400">
              Limited Time
            </div>
          </div>
          <div className="mt-4 flex items-baseline justify-center gap-x-2">
            <span className="text-5xl font-bold tracking-tight text-slate-900 dark:text-white">$99</span>
            <span className="text-sm font-semibold leading-6 text-slate-500 dark:text-slate-400">/one-time</span>
          </div>
          <p className="mt-6 text-base leading-7 text-slate-600 dark:text-slate-400">
            Get early access to AgencyOS Agency-in-a-Box and $200 worth of RaaS credits.
          </p>
          <ul role="list" className="mt-8 space-y-3 text-sm leading-6 text-slate-600 dark:text-slate-400">
            {[
              "Agency-in-a-Box License (Lifetime)",
              "$200 RaaS Credits included",
              "Priority Support",
              "Access to Private Community",
              "All standard recipes included",
              "Early access to new features"
            ].map((feature) => (
              <li key={feature} className="flex gap-x-3">
                <svg className="h-6 w-5 flex-none text-indigo-600 dark:text-indigo-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                </svg>
                {feature}
              </li>
            ))}
          </ul>
          <CheckoutButton />
          <p className="mt-6 text-xs leading-5 text-slate-500 dark:text-slate-400 text-center">
            Invoices and receipts available for easy company reimbursement.
          </p>
        </div>
      </div>
    </section>
  );
}
