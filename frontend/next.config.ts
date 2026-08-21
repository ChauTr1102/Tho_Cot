import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Produces a minimal .next/standalone server bundle for Docker deployments.
  output: "standalone",
};

export default nextConfig;
