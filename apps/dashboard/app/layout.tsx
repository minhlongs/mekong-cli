import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { SyntheticDataBanner } from '@/components/ui/synthetic-data-banner';
import './globals.css';

export const metadata: Metadata = {
  title: 'Mekong AI OS — IDE (Synthetic Pilot Demo)',
  description: '22 departments. 323 commands. AI-operated business platform — Synthetic Demo Data.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-white antialiased">
        <div className="mx-auto max-w-7xl px-4 pt-4">
          <SyntheticDataBanner />
        </div>
        {children}
      </body>
    </html>
  );
}
