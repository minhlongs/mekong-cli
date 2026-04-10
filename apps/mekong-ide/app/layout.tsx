import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mekong IDE",
  description: "AI-powered multi-agent development environment",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
