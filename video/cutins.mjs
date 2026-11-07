// Real site panels as 2x stills for the film's cut-ins (light mode). Usage: node video/cutins.mjs
import { chromium } from "playwright-core";
import path from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE = path.join(ROOT, "site"), OUT = path.join(ROOT, "video", "film", "assets", "site");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const after = (h) => `(() => { const e = [...document.querySelectorAll('h2')].find(x => x.textContent.trim() === ${JSON.stringify(h)}); return e.nextElementSibling; })()`;
const SHOTS = [
  ["p001_handoff_removed", "p/P001.html", after("Written handoff"), "document.querySelectorAll('details').forEach(d => { if (d.textContent.includes('could not support')) d.open = true; })"],
  ["p001_handoff_top", "p/P001.html", "document.querySelector('.sent')", ""],
  ["p001_banner", "p/P001.html", "document.querySelector('.banner')", ""],
  ["p001_crosschecks", "p/P001.html", after("Independent cross-checks"), ""],
  ["p001_metformin", "p/P001.html", "[...document.querySelectorAll('details')].find(d => d.querySelector('summary').textContent.includes('Metformin'))", "[...document.querySelectorAll('details')].forEach(d => { if (d.querySelector('summary').textContent.includes('Metformin')) d.open = true; })"],
  ["p019_handoff", "p/P019.html", after("Written handoff"), ""],
];
const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const ctx = await browser.newContext({ viewport: { width: 900, height: 900 }, deviceScaleFactor: 2, colorScheme: "light" });
const page = await ctx.newPage();
for (const [name, file, sel, prep] of SHOTS) {
  await page.goto("file://" + path.join(SITE, file));
  if (prep) await page.evaluate(prep);
  const el = await page.evaluateHandle(sel);
  await el.asElement().screenshot({ path: path.join(OUT, name + ".png") });
  console.log(name);
}
await browser.close();
