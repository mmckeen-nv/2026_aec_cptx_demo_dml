import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep the live dashboard cache separate from production builds. Running
  // `next build` must never leave the open control plane on stale assets.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
