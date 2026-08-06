/**
 * Render the README's mermaid diagrams as slide-ready PNGs.
 *
 * The deck needs an architecture diagram and a sequence diagram, and pasting a GitHub screenshot
 * of one into a slide gives you a blurry image with the wrong background. This renders them from
 * the same source the README uses — so the deck and the repo cannot show different diagrams — at
 * 3x on a transparent background, sized for a 10 x 5.625in slide.
 *
 *   node diagrams.mjs <repo-root> <out-dir>
 */

import puppeteer from "puppeteer-core";
import { readFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const ROOT = process.argv[2];
const OUT = process.argv[3];
mkdirSync(OUT, { recursive: true });

// Newlines normalised first. The repo checks out CRLF on Windows and the fence pattern
// below looks for a bare LF, so without this the match set is empty. Python's
// universal-newline reader hides that; Node's readFileSync does not.
const CR = String.fromCharCode(13);
const readme = readFileSync(join(ROOT, "README.md"), "utf8").split(CR).join("");
const blocks = [...readme.matchAll(/```mermaid\n([\s\S]*?)```/g)].map((m) => m[1]);
const [flow, seq] = blocks;

const page_html = (code, theme) => `<!doctype html>
<html><head><meta charset="utf-8">
<style>
  html,body{margin:0;padding:28px;background:transparent}
  #d{display:inline-block}
  .mermaid{font-family:'Segoe UI',system-ui,sans-serif}
</style>
</head><body>
<div id="d"><pre class="mermaid">${code.replace(/</g, "&lt;")}</pre></div>
<script type="module">
  import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
  mermaid.initialize({
    startOnLoad: true,
    theme: ${JSON.stringify(theme)},
    themeVariables: { fontSize: "17px", fontFamily: "Segoe UI, system-ui, sans-serif" },
    flowchart: { curve: "basis", nodeSpacing: 46, rankSpacing: 58, useMaxWidth: false },
    sequence: { useMaxWidth: false, boxMargin: 12, actorMargin: 62, messageFontSize: 15 },
  });
  await mermaid.run();
  window.__done = true;
</script>
</body></html>`;

const browser = await puppeteer.launch({
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: "new",
});

for (const [name, code, theme] of [
  ["architecture", flow, "default"],
  ["architecture-dark", flow, "dark"],
  ["sequence", seq, "default"],
  ["sequence-dark", seq, "dark"],
]) {
  const page = await browser.newPage();
  // 3x so a diagram scaled to fill a slide still has real pixels behind it.
  await page.setViewport({ width: 1800, height: 1200, deviceScaleFactor: 3 });
  await page.setContent(page_html(code, theme), { waitUntil: "networkidle0" });
  await page.waitForFunction("window.__done === true", { timeout: 30000 });
  await new Promise((r) => setTimeout(r, 400));

  const el = await page.$("#d");
  await el.screenshot({ path: join(OUT, `${name}.png`), omitBackground: true });
  const box = await el.boundingBox();
  console.log(`${name}.png  ${Math.round(box.width)}x${Math.round(box.height)} css @3x`);
  await page.close();
}

await browser.close();
