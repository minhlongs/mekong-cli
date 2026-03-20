/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  typescript: {
    ignoreBuildErrors: true, // M1 16GB: TS worker killed by OOM during build
  },
  images: {
    unoptimized: true,
  },
  // Disable Turbopack due to workspace root issue
  // turbopack: {
  //   root: __dirname,
  // },
}

module.exports = nextConfig
