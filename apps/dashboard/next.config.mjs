/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {},
  images: {
    unoptimized: true,
  },
  // Allow build without env vars — degrade gracefully
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  },
};

export default nextConfig;
