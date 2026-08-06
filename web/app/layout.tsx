import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Warrant — governed autonomous operations on Snowflake",
  description:
    "An operations agent whose authority is derived from the governance tags on the data it " +
    "touches, read live and resolved again at execution time. Public read-only viewer.",
  openGraph: {
    title: "Warrant — no action without a warrant",
    description:
      "An operations agent whose permission to act is read from Snowflake object tags, live " +
      "and again at execution time — so a human's approval cannot outlive the policy it was " +
      "granted under.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#131211" },
    { media: "(prefers-color-scheme: light)", color: "#f1ece1" },
  ],
};

/**
 * Resolve the theme before first paint.
 *
 * Without this the server sends dark markup, the client reads localStorage, and a reader
 * who prefers light sees a dark flash on every navigation. The script is deliberately
 * tiny and synchronous in <head>: it must finish before the browser paints, so it cannot
 * be a module, a component, or an effect.
 *
 * It writes an explicit value in every case, which is what lets globals.css carry exactly
 * two theme blocks instead of two plus a media query that has to be excluded whenever an
 * explicit choice disagrees with the OS.
 */
const THEME_BOOT = `(function(){try{
var s=localStorage.getItem('warrant-theme');
var t=(s==='light'||s==='dark')?s:(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
var e=document.documentElement;e.setAttribute('data-theme',t);e.style.colorScheme=t;
}catch(_){document.documentElement.setAttribute('data-theme','dark');}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT }} />
      </head>
      <body>
        <a
          href="#pass"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:border focus:border-[var(--line-hi)] focus:bg-[var(--page)] focus:px-4 focus:py-2 focus:text-sm"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
