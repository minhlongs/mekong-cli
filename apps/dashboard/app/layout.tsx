import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'MEKONG OPC 2027 — Sovereign Operating System & Agentic Cockpit',
  description:
    'Global Platform for One-Person Companies. Declarative Business Packs (opc-pack/v1), Payload-Bound SHA-256 Approvals, Honest Usage Economics & Dual-Rail RaaS.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#06080d] text-white antialiased selection:bg-emerald-500/30">
        {children}
      </body>
    </html>
  );
}
