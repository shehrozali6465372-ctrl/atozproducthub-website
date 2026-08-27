import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@atoz/design-system"],
  output: "standalone",
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
