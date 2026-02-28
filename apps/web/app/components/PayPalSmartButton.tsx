"use client";

// PayPal is REMOVED per project rules. Use Polar.sh instead.
// See: .claude/rules/payment-provider.md

interface PayPalSmartButtonProps {
  amount?: string;
  currency?: string;
  planId?: string;
  description?: string;
  customerEmail?: string;
  tenantId?: string;
  mode?: "payment" | "subscription";
  onSuccess?: (details: unknown) => void;
  onError?: (err: unknown) => void;
  apiBaseUrl?: string;
}

export default function PayPalSmartButton(_props: PayPalSmartButtonProps) {
  return (
    <div className="p-4 text-center text-sm text-gray-500">
      Payment processing via Polar.sh. PayPal has been removed.
    </div>
  );
}
