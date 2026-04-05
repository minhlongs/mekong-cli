/** @type {import('next').NextConfig} */
const nextConfig = {
<<<<<<< HEAD
  experimental: {},
  images: {
    unoptimized: true,
  },
  // Allow build without env vars — degrade gracefully
=======
  images: { unoptimized: true },
>>>>>>> main
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  },
};
<<<<<<< HEAD

export default nextConfig;
=======
export default nextConfig;
>>>>>>> main
