"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";

function CheckoutForm() {
  const searchParams = useSearchParams();
  const tier = searchParams.get("tier") || "pro";

  const [email, setEmail] = useState("");

  const prices = {
    starter: { amount: "29", name: "Starter Agency", mode: "subscription" },
    pro: { amount: "99", name: "Pro Agency", mode: "subscription" },
    franchise: { amount: "299", name: "Franchise", mode: "subscription" },
    enterprise: { amount: "999", name: "Enterprise", mode: "subscription" },
  };

  const selectedPrice = prices[tier as keyof typeof prices] || prices.pro;

  return (
    <div className="space-y-6">
      {/* Product Info */}
      <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700">
        <h2 className="text-2xl font-bold mb-2">{selectedPrice.name}</h2>
        <div className="text-4xl font-bold text-emerald-400">
          ${selectedPrice.amount}
          <span className="text-lg text-slate-500 ml-2 font-normal">
            {selectedPrice.mode === 'subscription' ? '/tháng' : ''}
          </span>
        </div>
        <p className="text-slate-400 mt-2">
          {selectedPrice.mode === 'subscription' ? 'Hủy bất cứ lúc nào' : 'Thanh toán 1 lần, sở hữu trọn đời'}
        </p>
      </div>

      {/* Email Input */}
      <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700">
        <label className="block text-sm font-medium mb-2">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full px-4 py-3 rounded-lg bg-slate-700 border border-slate-600 focus:border-emerald-500 focus:outline-none"
          placeholder="your@email.com"
        />
      </div>

      {/* Payment placeholder - Stripe integration to be added */}
      <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 text-center">
        <p className="text-slate-400">Stripe checkout integration coming soon</p>
      </div>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <div className="min-h-screen bg-linear-to-b from-slate-900 to-slate-800 text-white py-20">
      <div className="container mx-auto px-6 max-w-2xl">
        <h1 className="text-4xl font-bold mb-8 text-center">Thanh Toán</h1>

        <Suspense fallback={<div className="text-center">Loading...</div>}>
          <CheckoutForm />
        </Suspense>

        <div className="mt-8 text-center">
          <Link href="/" className="text-emerald-400 hover:underline">
            ← Quay lại trang chủ
          </Link>
        </div>
      </div>
    </div>
  );
}
