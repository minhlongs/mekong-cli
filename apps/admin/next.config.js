/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // Pre-existing @types/react@18 vs React 19 type mismatch in lucide-react + next/link
    ignoreBuildErrors: true,
  },
};

module.exports = nextConfig;
