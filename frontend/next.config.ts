import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Produces a minimal .next/standalone server bundle for Docker deployments.
  output: "standalone",
  allowedDevOrigins: ['http://*', 'https://*', '172.20.10.12'],
};

export default nextConfig;
