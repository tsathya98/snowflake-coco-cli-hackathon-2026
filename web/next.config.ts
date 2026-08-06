import type { NextConfig } from "next";

const config: NextConfig = {
  // snowflake-sdk is a native-ish Node driver: it must not be traced into the
  // client bundle or bundled by turbopack, or the build fails resolving `net`.
  serverExternalPackages: ["snowflake-sdk"],
  poweredByHeader: false,

  // A stable public URL for the demo video, so the address submitted to the judging
  // portal never has to change even if the recording is re-uploaded. Temporary on
  // purpose (307): the destination is expected to move, and a permanent redirect
  // would be cached by browsers that had already followed it once.
  async redirects() {
    return [
      {
        source: "/demo-video",
        destination: process.env.DEMO_VIDEO_URL ?? "/",
        permanent: false,
      },
    ];
  },
};

export default config;
