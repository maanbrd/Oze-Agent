import type { NextConfig } from "next";

// @ts-expect-error -- dependency-free .mjs module (shared with node:test); no .d.ts
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
