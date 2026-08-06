// Render the submission deck to a print-ready PDF.
// The deck is a self-contained artifact bundle: 7 slides at 1920x1080. The portal
// takes a PDF under 5 MB, so each slide becomes one landscape page at exact size.
import puppeteer from "puppeteer-core";
import { pathToFileURL } from "node:url";

const SRC = "docs/submission/warrant-submission-deck.html";
const OUT = "docs/submission/warrant-submission-deck.pdf";

const browser = await puppeteer.launch({
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  headless: "new",
  args: ["--allow-file-access-from-files", "--font-render-hinting=none"],
});
const page = await browser.newPage();
await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
await page.goto(pathToFileURL(SRC).href, { waitUntil: "networkidle0", timeout: 120000 });
await new Promise((r) => setTimeout(r, 4000));

const n = await page.evaluate(() => document.querySelectorAll("[data-slide], section, .slide").length);
console.log("slide-ish elements:", n);

await page.pdf({
  path: OUT,
  width: "1920px",
  height: "1080px",
  printBackground: true,
  preferCSSPageSize: false,
  margin: { top: 0, right: 0, bottom: 0, left: 0 },
});
await browser.close();
console.log("wrote", OUT);
