import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'Mekong AI OS — IDE',
  description: '22 departments. 323 commands. AI-operated business platform.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-white antialiased">
        {children}
      </body>
    </html>
  );
}
