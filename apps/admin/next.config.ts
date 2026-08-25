import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The shared design system ships TypeScript source (ADR-0001).
  transpilePackages: ["@atoz/design-system"],
  output: "standalone",
};

export default nextConfig;
