import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mekong IDE — The One-Person Company Platform",
  description:
    "Replace a 50-person team with autonomous agents. 443 commands across 10 business layers.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
