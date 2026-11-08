// Record the live Clocked demo site for the teaser, frame by frame (Playwright screenshots, no screen recorder).
// The page runs in a 560x350 CSS window at device scale 3.43, so every frame is a sharp 1920x1200 screenshot and the
// page's 16 px text shows at ~27 px in a 960 px panel. Mouse, scroll and the click ring are stepped one frame at a time
// at 30 fps, so every run gives the same clip. The cursor is drawn in the page and follows the real mouse.
// Output: assets/clips/<name>.mp4.   Usage: node record.mjs [clip ...]
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const SITE = "https://drahmed7887.github.io/hack-clocked/";
const W = 560, H = 350, DSF = 1920 / 560, FPS = 30;
const OUT = join(dirname(fileURLToPath(import.meta.url)), "assets", "clips");

const CURSOR = `(() => {
  const add = () => {
    if (document.getElementById('hf-cursor')) return;
    const c = document.createElement('div');
    c.id = 'hf-cursor';
    c.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24"><path d="M4 2 L4 19 L8.5 15 L11.5 22 L14.5 20.7 L11.6 14 L18 14 Z" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    c.style.cssText = 'position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;transform:translate(-99px,-99px)';
    const r = document.createElement('div');
    r.id = 'hf-ring';
    r.style.cssText = 'position:fixed;left:0;top:0;width:30px;height:30px;margin:-15px 0 0 -15px;border-radius:50%;border:2px solid rgb(232,163,61);opacity:0;z-index:2147483646;pointer-events:none';
    document.body.append(r, c);
    window.__cur = (x, y, ring) => {
      c.style.transform = 'translate(' + (x - 3) + 'px,' + (y - 2) + 'px)';
      r.style.left = x + 'px'; r.style.top = y + 'px';
      r.style.opacity = ring > 0 ? String(1 - ring) : '0';
      r.style.transform = 'scale(' + (0.4 + ring * 1.1) + ')';
    };
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
})();`;

const ease = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

class Shot {
  constructor(page, dir) { this.page = page; this.dir = dir; this.n = 0; this.x = W * 0.8; this.y = H * 0.3; }
  async frame(ring = 0) {
    await this.page.evaluate(([x, y, r]) => window.__cur && window.__cur(x, y, r), [this.x, this.y, ring]);
    await this.page.screenshot({ path: join(this.dir, `${String(this.n++).padStart(4, "0")}.jpg`), type: "jpeg", quality: 92 });
  }
  async hold(sec) { for (let i = 0; i < Math.round(sec * FPS); i++) await this.frame(); }
  async move(x, y, sec = 0.8) {
    const [x0, y0] = [this.x, this.y], n = Math.round(sec * FPS);
    for (let i = 1; i <= n; i++) {
      const e = ease(i / n);
      this.x = x0 + (x - x0) * e; this.y = y0 + (y - y0) * e;
      await this.page.mouse.move(this.x, this.y);
      await this.frame();
    }
  }
  async moveTo(sel, sec = 0.8, fx = 0.5) {
    const b = await this.page.locator(sel).first().boundingBox();
    await this.move(b.x + b.width * fx, b.y + b.height / 2, sec);
  }
  async scroll(sel, frac = 0.2, sec = 1.0) {
    const [start, target] = await this.page.evaluate(([sel, frac]) => {
      const el = document.querySelector(sel);
      return [scrollY, Math.max(0, scrollY + el.getBoundingClientRect().top - innerHeight * frac)];
    }, [sel, frac]);
    const n = Math.round(sec * FPS);
    for (let i = 1; i <= n; i++) {
      await this.page.evaluate(y => scrollTo(0, y), start + (target - start) * ease(i / n));
      await this.frame();
    }
  }
  async click(after) {                       // a real click; the ring plays over the next 0.4 s
    await this.page.mouse.down(); await this.page.mouse.up();
    if (after) await after();
    const n = Math.round(0.4 * FPS);
    for (let i = 1; i <= n; i++) await this.frame(i / n);
  }
}

const P001 = SITE + "p/P001.html";
const CLIPS = {
  async records(s, page) {
    await page.goto(SITE, { waitUntil: "networkidle" });
    await page.evaluate(() => { const t = document.querySelector("table"); scrollTo(0, scrollY + t.getBoundingClientRect().top - 24); });
    await s.hold(0.5);
    await s.moveTo("a[href='p/P001.html']", 0.8);
    await s.hold(0.2);
    await s.click(async () => { await page.waitForURL("**/p/P001.html"); await page.waitForLoadState("networkidle"); });
    await s.hold(0.3);
    await s.moveTo("main .card li:nth-of-type(4)", 1.0, 0.9);
    await s.hold(2.0);
  },
  async conflict(s, page) {
    await page.goto(P001, { waitUntil: "networkidle" });
    await page.evaluate(() => { const b = document.querySelector(".banner"); scrollTo(0, scrollY + b.getBoundingClientRect().top - innerHeight * 0.5); });
    await s.hold(0.2);
    await s.scroll(".banner", 0.12, 0.8);
    await s.moveTo(".banner q >> nth=0", 0.7, 0.9);
    await s.hold(0.7);
    await s.moveTo(".banner q >> nth=1", 0.7, 0.9);
    await s.hold(1.5);
  },
  async verify(s, page) {
    await page.goto(P001, { waitUntil: "networkidle" });
    await s.hold(0.2);
    await s.scroll("main > h2", 0.04, 1.1);
    await s.hold(0.5);
    await s.scroll("main .card details", 0.45, 1.0);
    await s.moveTo("main .card details summary", 0.7, 0.4);
    await s.hold(0.2);
    await s.click(() => page.waitForTimeout(80));             // opens "Removed"
    await s.scroll("main .card details", 0.25, 0.8);
    await s.move(W * 0.93, H * 0.9, 0.5);                      // cursor out of the way of the removed sentence
    await s.hold(1.5);
  },
  async meds(s, page) {
    await page.goto(P001, { waitUntil: "networkidle" });
    await page.evaluate(() => document.querySelectorAll("main > details").forEach(d => { d.open = false; }));
    await page.locator("main > details").first().evaluate(e => { e.id = "hf-warf"; });   // Warfarin, closed so the click opens it
    await page.evaluate(() => { const w = document.querySelector("#hf-warf"); scrollTo(0, scrollY + w.getBoundingClientRect().top - innerHeight * 0.6); });
    await s.hold(0.2);
    await s.scroll("#hf-warf", 0.12, 0.8);
    await s.moveTo("#hf-warf summary", 0.7, 0.45);
    await s.hold(0.2);
    await s.click(() => page.waitForTimeout(80));             // opens Warfarin
    await s.moveTo("#hf-warf li:last-of-type", 0.9, 0.6);
    await s.hold(2.0);
  },
};

const names = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(CLIPS);
mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
for (const name of names) {
  const dir = join(OUT, `_${name}`);
  rmSync(dir, { recursive: true, force: true });
  mkdirSync(dir, { recursive: true });
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DSF });
  await ctx.addInitScript(CURSOR);
  const page = await ctx.newPage();
  const shot = new Shot(page, dir);
  await CLIPS[name](shot, page);
  await ctx.close();
  const mp4 = join(OUT, `${name}.mp4`);
  execFileSync("ffmpeg", ["-loglevel", "error", "-y", "-framerate", String(FPS), "-i", join(dir, "%04d.jpg"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "14", mp4]);
  rmSync(dir, { recursive: true, force: true });
  console.log(`${name}: ${shot.n} frames, ${(shot.n / FPS).toFixed(1)} s`);
}
await browser.close();
