import type { NextConfig } from "next";

const config: NextConfig = {
  // snowflake-sdk is a native-ish Node driver: it must not be traced into the
  // client bundle or bundled by turbopack, or the build fails resolving `net`.
  serverExternalPackages: ["snowflake-sdk"],
  poweredByHeader: false,
};

export default config;
