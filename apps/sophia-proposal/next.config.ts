import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloudflare Pages compatibility
  output: 'standalone',
  images: {
    unoptimized: true,
    disableStaticImages: true
  },
  // Bundle Optimization - removeConsole in production
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },
  // Disable ISR for static export
  onDemandEntries: {
    maxInactiveAge: 60 * 1000,
    pagesBufferLength: 2,
  },
};

export default nextConfig;
