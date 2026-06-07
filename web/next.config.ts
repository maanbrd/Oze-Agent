import type { NextConfig } from "next";

// Dependency-free .mjs module (shared with the node:test unit test).
import { buildSecurityHeaders } from "./lib/security-headers.mjs";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async headers() {
    return [
      {
        // Apply security headers to every route.
        source: "/(.*)",
        headers: buildSecurityHeaders(),
      },
    ];
  },
};

export default nextConfig;
