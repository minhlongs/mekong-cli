import type { NextConfig } from "next";

const config: NextConfig = {
  output: "export",
  basePath: "/ide",
  images: { unoptimized: true },
};

export default config;
