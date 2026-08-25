import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@atoz/design-system"],
  output: "standalone",
};

export default nextConfig;
