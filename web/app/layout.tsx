import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Warrant — governed autonomous operations on Snowflake",
  description:
    "An operations agent whose authority is derived from the governance tags on the data it " +
    "touches, read live and resolved again at execution time. Public read-only viewer.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
