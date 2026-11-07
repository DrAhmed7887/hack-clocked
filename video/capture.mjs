// Scripted capture of the static site (plan: Drive Zayed OS/Hackathons/2026-11-clocked/video/PLAN.md).
// Stills per state, 30 fps frames only for the three moves. Output: runs/video/frames/ + runs/video/timeline.json
import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SITE = path.join(ROOT, "site");
const OUT = path.join(ROOT, "runs", "video", "frames");
const AUDIO = path.join(ROOT, "runs", "video", "audio");
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const LEAD = 0.25, TAIL = 0.45, FPS = 30;
const RAIL = ["Protect", "Extract", "rules", "Fill", "Verify", "Compare"];

const FILM_CSS = `
html{scrollbar-width:none}html::-webkit-scrollbar{display:none}body{padding-top:44px}*{caret-color:transparent}
#film{position:fixed;inset:0;pointer-events:none;z-index:9999;font:15px/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
#rail{position:absolute;top:0;left:0;right:0;height:44px;background:#f6f5f1;border-bottom:1px solid #e2e0d8;display:flex;gap:28px;align-items:center;justify-content:center;letter-spacing:.02em}
#rail span{color:#5d5d58;padding:4px 0}#rail span.on{color:#1d1d1b;font-weight:600;border-bottom:2px solid #1d1d1b}
#box{position:absolute;border:2px solid #1d1d1b;border-radius:8px;display:none}
.tag{position:absolute;background:#fff;color:#1d1d1b;border:1px solid #1d1d1b;border-radius:6px;padding:5px 9px;font-size:14px}
#endband{position:absolute;left:0;right:0;bottom:96px;text-align:center;color:#1d1d1b;font-size:16px;line-height:1.5;display:none;background:rgba(246,245,241,.96);padding:10px 0;border-top:1px solid #e2e0d8}`;

function meta(id) { return JSON.parse(fs.readFileSync(path.join(AUDIO, `${id}.json`), "utf8")); }

async function open(page, file, { rail = false } = {}) {
  await page.goto("file://" + path.join(SITE, file));
  await page.addStyleTag({ content: FILM_CSS });
  await page.evaluate(({ rail, names }) => {
    document.documentElement.style.zoom = "1.25";
    const film = document.createElement("div");
    film.id = "film";
    film.innerHTML = `<div id="rail" style="display:${rail ? "flex" : "none"}">${names.map(n => `<span data-n="${n}">${n}</span>`).join("")}</div><div id="box"></div><div id="endband"></div>`;
    document.body.appendChild(film);
    document.querySelectorAll("details").forEach(d => (d.open = false));
    // helpers
    window.__find = (sel, text, nth = 0) => {
      const hits = [...document.querySelectorAll(sel)].filter(e => e.textContent.includes(text));
      return hits.sort((a, b) => a.textContent.length - b.textContent.length)[nth] || hits[0];
    };
    window.__textRect = (container, text) => {
      const w = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      let n; while ((n = w.nextNode())) { const i = n.data.indexOf(text); if (i >= 0) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + text.length); return r.getBoundingClientRect(); } }
      return null;
    };
  }, { rail, names: ["Protect", "Extract", "rules", "Fill", "Verify", "Compare"] });
}

const ev = (page, fn, arg) => page.evaluate(fn, arg);
const rail = (page, active) => ev(page, a => { document.getElementById("rail").style.display = a === "off" ? "none" : "flex";
  document.querySelectorAll("#rail span").forEach(s => s.classList.toggle("on", s.dataset.n === a)); }, active);
const boxOff = page => ev(page, () => { document.getElementById("box").style.display = "none"; });
// rect in CSS px of the viewport, accounting for zoom (getBoundingClientRect is already zoomed in Chrome)
async function boxRects(page, rects) {
  await ev(page, rs => {
    const z = parseFloat(document.documentElement.style.zoom || "1");
    const r = rs.filter(Boolean).reduce((a, b) => ({ left: Math.min(a.left, b.left), top: Math.min(a.top, b.top),
      right: Math.max(a.right, b.right), bottom: Math.max(a.bottom, b.bottom) }));
    const b = document.getElementById("box"), pad = 6;
    // getBoundingClientRect reports zoomed px, and the film layer is zoomed again: divide (measured 7 Nov)
    Object.assign(b.style, { display: "block", left: (r.left / z - pad) + "px", top: (r.top / z - pad) + "px",
      width: ((r.right - r.left) / z + 2 * pad) + "px", height: ((r.bottom - r.top) / z + 2 * pad) + "px" });
  }, rects);
}
const rectOf = (page, sel, text, nth = 0) => ev(page, ({ sel, text, nth }) => {
  const e = window.__find(sel, text, nth); if (!e) return null; const r = e.getBoundingClientRect();
  return { left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }, { sel, text, nth });
const textRect = (page, sel, within, text) => ev(page, ({ sel, within, text }) => {
  const c = window.__find(sel, within); const r = c && window.__textRect(c, text);
  return r && { left: r.left, top: r.top, right: r.right, bottom: r.bottom }; }, { sel, within, text });
// Self-correcting scroll: measure how far the element actually moved and correct, whatever the zoom units are.
const scrollTo = (page, sel, text, frac = 0.3) => ev(page, ({ sel, text, frac }) => {
  const e = window.__find(sel, text); let k = 1;
  for (let i = 0; i < 4; i++) {
    const before = e.getBoundingClientRect().top, want = before - innerHeight * frac;
    if (Math.abs(want) < 2) break;
    window.scrollBy(0, want * k);
    const moved = before - e.getBoundingClientRect().top;
    if (Math.abs(moved) > 1) k = k * want / moved;
  } }, { sel, text, frac });
const openDetails = (page, text) => ev(page, t => { const s = window.__find("summary", t); s.parentElement.open = true; s.blur(); }, text);
const tag = (page, id, text, pos) => ev(page, ({ id, text, pos }) => {
  let t = document.getElementById(id); if (!t) { t = document.createElement("div"); t.id = id; t.className = "tag"; document.getElementById("film").appendChild(t); }
  t.textContent = text; Object.assign(t.style, pos); }, { id, text, pos });
const untag = (page, id) => ev(page, i => document.getElementById(i)?.remove(), id);
const scale = (page, s, ox, oy) => ev(page, ({ s, ox, oy }) => { const m = document.querySelector("main");
  m.style.transformOrigin = `${ox}px ${oy}px`; m.style.transform = `scale(${s})`; }, { s, ox, oy });

const origin = (page, r) => ev(page, r => { const m = document.querySelector("main").getBoundingClientRect();
  const z = parseFloat(document.documentElement.style.zoom || "1");
  return [((r.left + r.right) / 2 - m.left) / z, ((r.top + r.bottom) / 2 - m.top) / z]; }, r);
const ease = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
let counter = 0;
async function still(page, dir) { const f = path.join(dir, `s${String(counter++).padStart(4, "0")}.png`); await page.screenshot({ path: f }); return f; }
async function move(page, dir, seconds, stepFn) {
  const files = [], n = Math.round(seconds * FPS);
  for (let i = 0; i <= n; i++) { await stepFn(ease(i / n)); files.push(await still(page, dir)); }
  return files;
}

// Each shot: setup, then beats [cueName, async action, optional move seconds]
const SHOTS = {
  S1: { file: "p/P001.html", rail: false, setup: async p => {
      await openDetails(p, "Pharmacy record, 2025-04-17"); await openDetails(p, "GP letter, 2025-12-25");
      await scrollTo(p, "pre", "sulfonamides (hives)", 0.4); await tag(p, "t1", "Synthetic record", { top: "56px", left: "16px" }); },
    beats: {
      box_pharm: async p => boxRects(p, [await textRect(p, "pre", "sulfonamides (hives)", "Allergies: sulfonamides (hives)")]),
      scroll_to_gp: { move: 3, fn: async (p, dir) => { await boxOff(p); const y0 = await ev(p, () => scrollY);
        const y1 = await ev(p, () => { const e = window.__find("pre", "Sin alergias"); const z = parseFloat(document.documentElement.style.zoom);
          return scrollY + (e.getBoundingClientRect().top + 120 - innerHeight * 0.4) / z; });
        return move(p, dir, 3, async t => ev(p, y => window.scrollTo(0, y), y0 + (y1 - y0) * t)); } },
      box_gp: async p => boxRects(p, [await textRect(p, "pre", "Sin alergias", "Sin alergias medicamentosas conocidas.")]) } },
  S2: { file: "index.html", rail: "none", setup: async p => {},
    beats: { box_row: async p => boxRects(p, [await rectOf(p, "tr", "P001")]) } },
  S3: { file: "p/P001.html", rail: "Protect", setup: async p => {}, beats: {
      rail_protect: async p => rail(p, "Protect"),
      pushin_banner: { move: 0.8, fn: async (p, dir) => { const r = await rectOf(p, ".banner", "Allergy conflict");
        const [ox, oy] = await origin(p, r);
        return move(p, dir, 0.8, async t => scale(p, 1 + 0.35 * t, ox, oy)); } } } },
  S4: { file: "p/P001.html", rail: "Extract", setup: async p => { await openDetails(p, "Warfarin"); await openDetails(p, "Bisoprolol");
      await scrollTo(p, "h2", "Medications", 0.12); }, beats: {
      rail_extract: async p => rail(p, "Extract"), rail_rules: async p => rail(p, "rules"),
      box_warfarin: async p => boxRects(p, [await rectOf(p, "details", "Warfarin")]),
      box_bisoprolol: async p => boxRects(p, [await rectOf(p, "details", "Bisoprolol")]) } },
  S5: { file: "p/P001.html", rail: "Fill", setup: async p => { await scrollTo(p, "h2", "Written handoff", 0.1); }, beats: {
      rail_fill: async p => rail(p, "Fill"),
      rail_verify_box_verified: async p => { await rail(p, "Verify"); const rs = [];
        for (let i = 0; i < 3; i++) rs.push(await rectOf(p, ".sent", "Verified in the records", i)); await boxRects(p, rs); },
      open_removed: async p => { await openDetails(p, "Sentences the checker could not support");
        await boxRects(p, [await rectOf(p, "details", "Sentences the checker could not support")]); },
      box_rebuilt: async p => boxRects(p, [await rectOf(p, ".sent", "Added by rules")]) } },
  S6: { file: "p/P001.html", rail: "rules", setup: async p => { await openDetails(p, "Metformin"); await scrollTo(p, "details", "Metformin", 0.25); }, beats: {
      pushin_metformin: { move: 0.8, fn: async (p, dir) => { const r = await rectOf(p, "details", "Metformin");
        const [ox, oy] = await origin(p, r);
        const files = await move(p, dir, 0.8, async t => scale(p, 1 + 0.3 * t, ox, oy));
        return files; } },
      tag_baseline: async p => tag(p, "t2", "Medication labels, realistic set: 54/100 without normalisation → 100/100 with it · eval/score.py",
        { right: "16px", bottom: "110px" }) } },
  S7: { file: "p/P001.html", rail: "Compare", setup: async p => { await scrollTo(p, "h2", "Independent cross-checks", 0.15);
      await tag(p, "t3", "Across 20 patients: Protect 20/20 · Compare 25/39", { right: "16px", top: "56px" }); }, beats: {
      box_compare: async p => boxRects(p, [await rectOf(p, "p", "Clocked Compare")]) } },
  S8: { file: "p/P019.html", rail: "Verify", setup: async p => { await scrollTo(p, "h2", "Written handoff", 0.1);
      await tag(p, "t4", "Another synthetic patient · P019", { right: "16px", top: "56px" }); }, beats: {
      box_lisinopril: async p => boxRects(p, [await rectOf(p, ".sent", "Lisinopril is listed")]),
      box_unknown: async p => boxRects(p, [await rectOf(p, ".sent", "No record mentions allergies")]) } },
  S9: { file: "method.html", rail: "off", setup: async p => { await scrollTo(p, "h2", "Measured results on realistic wording", 0.08); }, beats: {
      box_m100: async p => boxRects(p, [await rectOf(p, "li", "Medication labels correct: 100/100")]),
      box_m5: async p => boxRects(p, [await rectOf(p, "li", "Allergy conflicts flagged: 5/5")]),
      box_m70: async p => { await scrollTo(p, "li", "Discrepancies named in the final text", 0.45);
        await boxRects(p, [await rectOf(p, "li", "Discrepancies named in the final text")]); },
      box_m55: async p => boxRects(p, [await rectOf(p, "li", "before rules R7a/R7b")]),
      box_m0: async p => boxRects(p, [await rectOf(p, "li", "Medicines named in the final text that are not in the records")]) } },
};

async function main() {
  fs.rmSync(OUT, { recursive: true, force: true });
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1.5, colorScheme: "light" });
  const page = await ctx.newPage();
  const timeline = [];
  let t0 = 0;
  for (const [id, shot] of Object.entries(SHOTS)) {
    const dir = path.join(OUT, id); fs.mkdirSync(dir, { recursive: true });
    const m = meta(id), dur = LEAD + m.duration + TAIL;
    await open(page, shot.file, { rail: shot.rail && shot.rail !== "off" });
    if (shot.rail && shot.rail !== "none" && shot.rail !== "off") await rail(page, "__none__");
    await shot.setup(page); await ev(page, () => document.activeElement?.blur());
    const segs = [{ t: 0, file: await still(page, dir) }];
    const beats = Object.entries(m.cues).sort((a, b) => a[1] - b[1]);
    for (const [name, at] of beats) {
      const b = shot.beats[name]; if (!b) throw new Error(`${id}: no action for cue ${name}`);
      const t = LEAD + at;
      if (typeof b === "function") { await b(page); segs.push({ t, file: await still(page, dir) }); }
      else { const files = await b.fn(page, dir); files.forEach((f, i) => segs.push({ t: t + i / FPS, file: f })); }
    }
    if (id === "S9") { // end band for the final 4 s
      await ev(page, () => { const e = document.getElementById("endband"); e.style.display = "block"; e.innerHTML =
        "Synthetic records only. Decision support for clinicians, not a diagnosis or a prescription.<br>github.com/DrAhmed7887/hack-clocked · Dr Ahmed Zayed, physician, health-informatics student"; });
      segs.push({ t: Math.max(LEAD + m.duration - 0.5, segs.at(-1).t + 0.1), file: await still(page, dir) });
    }
    timeline.push({ id, start: t0, duration: dur, segs });
    t0 += dur;
    console.log(id, "captured", segs.length, "frames,", dur.toFixed(2), "s");
  }
  await browser.close();
  fs.writeFileSync(path.join(ROOT, "runs", "video", "timeline.json"), JSON.stringify({ lead: LEAD, total: t0, shots: timeline }, null, 1));
  console.log("total", t0.toFixed(2), "s");
}
main().catch(e => { console.error(e); process.exit(1); });
