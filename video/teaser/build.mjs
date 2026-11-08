// Build the teaser's HyperFrames files from teaser.json (the reusable template).
// To make a teaser for another app: record its clips (record.mjs), edit teaser.json, run `node build.mjs`,
// then `npx hyperframes check`, `snapshot`, `render`. Edit the look here (CSS below), the content in teaser.json.
//
// Layout (square, 1080): a panel of real app footage (960x600, the clips' 16:10 shape) on a dark ground, one caption
// block under it (label, title, subtitle), a fixed frame (corners, brand, scene counter, progress line), music + sounds.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const T = JSON.parse(readFileSync(new URL("./teaser.json", import.meta.url)));
const S = T.size, A = T.accent;
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const br = s => esc(s).replace(/\n/g, "<br>");
const n2 = i => String(i).padStart(2, "0");
const f = x => Number(x.toFixed(3));

// ---- timing -------------------------------------------------------------------------------------------------
let t = 0;
const intro = { id: "intro", start: 0, duration: T.intro.duration }; t += T.intro.duration;
const scenes = T.scenes.map((s, i) => { const o = { ...s, n: i + 1, start: f(t) }; t += s.duration; return o; });
const end = { id: "end", start: f(t), duration: T.end.duration }; t += T.end.duration;
const TOTAL = f(t);

const BASE = `#root { position: absolute; inset: 0; overflow: hidden; font-family: "Inter", sans-serif; color: #F3F5F8; }
.lab { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 28px; letter-spacing: 0.14em; text-transform: uppercase; color: ${A}; }
.ttl { font-weight: 900; font-size: 56px; line-height: 1.06; letter-spacing: -0.025em; color: #FFFFFF; }
.sub { font-weight: 400; font-size: 30px; line-height: 1.3; color: #AEB6C4; }`;

const scene = (id, css, html, js) => `<template>
  <style>
${BASE}
${css}
  </style>
  <div id="root" data-composition-id="${id}" data-width="${S}" data-height="${S}">
${html}
  </div>
  <script>
    (function () {
      const tl = gsap.timeline({ paused: true });
      const rise = (sel, t, d = 0.5, y = 26) => tl.fromTo(sel, { opacity: 0, y: y, filter: "blur(6px)" }, { opacity: 1, y: 0, filter: "blur(0px)", duration: d, ease: "expo.out" }, t);
      const leave = (sel, t) => tl.to(sel, { opacity: 0, y: -14, filter: "blur(6px)", duration: 0.28, ease: "power3.in" }, t);
${js}
      window.__timelines["${id}"] = tl;
    })();
  </script>
</template>
`;

const caption = (id, s) => `    <div id="${id}-cap" class="cap">
      <div id="${id}-lab" class="lab">${n2(s.n)} · ${esc(s.label)}</div>
      <div id="${id}-ttl" class="ttl">${esc(s.title)}</div>
      <div id="${id}-sub" class="sub">${esc(s.sub)}</div>
    </div>`;
const CAP_CSS = `.cap { position: absolute; left: 84px; top: 772px; width: 912px; padding-left: 26px; border-left: 4px solid ${A}; }
.cap .ttl { margin-top: 12px; } .cap .sub { margin-top: 14px; }`;
const capIn = id => `      rise("#${id}-lab", 0.15, 0.45, 14); rise("#${id}-ttl", 0.25); rise("#${id}-sub", 0.42);`;

function clipScene(s) {
  const d = s.duration;
  const css = `${CAP_CSS}
.panel { position: absolute; left: 60px; top: 128px; width: 960px; height: 600px; border-radius: 22px; overflow: hidden;
  background: #F6F5F1; border: 1px solid rgba(255,255,255,0.16);
  box-shadow: 0 34px 90px rgba(0,0,0,0.6), 0 0 120px ${A}22; }
.cam { position: absolute; inset: 0; transform-origin: 50% 40%; }
.cam video { position: absolute; left: 0; top: 0; width: 960px; height: 600px; object-fit: cover; }`;
  const html = `    <div id="${s.id}-panel" class="panel">
      <div id="${s.id}-cam" class="cam" data-layout-allow-overflow>
        <video id="${s.id}-vid" class="clip" src="${s.clip}" data-start="0" data-duration="${d}" data-media-start="${s.mediaStart}" data-track-index="1" muted playsinline></video>
      </div>
    </div>
${caption(s.id, s)}`;
  const js = `      tl.fromTo("#${s.id}-panel", { opacity: 0, y: 44, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "expo.out" }, 0);
      tl.fromTo("#${s.id}-cam", { scale: 1 }, { scale: 1.06, duration: ${f(d - 0.3)}, ease: "none" }, 0);
${capIn(s.id)}
      leave("#${s.id}-panel", ${f(d - 0.32)}); leave("#${s.id}-cap", ${f(d - 0.32)});`;
  return scene(s.id, css, html, js);
}

function numbersScene(s) {
  const d = s.duration;
  const css = `${CAP_CSS}
.nums { position: absolute; left: 60px; top: 128px; width: 960px; height: 600px; display: flex; flex-direction: column; justify-content: center; gap: 48px; padding-left: 70px; }
.num .v { font-weight: 900; font-size: 168px; line-height: 0.95; letter-spacing: -0.045em; color: #FFFFFF; font-variant-numeric: tabular-nums; }
.num .v b { color: ${A}; font-weight: 900; }
.num .l { font-size: 34px; color: #AEB6C4; margin-top: 8px; }`;
  const nums = s.numbers.map((x, i) => {
    const [a, b] = x.value.split("/");
    return `      <div id="${s.id}-n${i}" class="num"><div class="v">${esc(a)}<b>/${esc(b)}</b></div><div class="l">${esc(x.label)}</div></div>`;
  }).join("\n");
  const html = `    <div id="${s.id}-nums" class="nums">
${nums}
    </div>
${caption(s.id, s)}`;
  const js = `${s.numbers.map((_, i) => `      rise("#${s.id}-n${i}", ${f(0.1 + i * 0.45)}, 0.6, 40);`).join("\n")}
${capIn(s.id)}
      leave("#${s.id}-nums", ${f(d - 0.32)}); leave("#${s.id}-cap", ${f(d - 0.32)});`;
  return scene(s.id, css, html, js);
}

function introScene() {
  const d = T.intro.duration;
  const css = `.wrap { position: absolute; left: 96px; top: 330px; width: 888px; }
.line { position: absolute; left: 96px; top: 300px; width: 888px; height: 4px; }
.k { margin-bottom: 26px; }
.big { font-weight: 900; font-size: 96px; line-height: 1.0; letter-spacing: -0.035em; }
.s2 { margin-top: 28px; }`;
  const html = `    <svg id="intro-line" class="line" viewBox="0 0 888 4" preserveAspectRatio="none"><path id="intro-path" d="M0 2 H888" stroke="${A}" stroke-width="4" fill="none" stroke-dasharray="888" stroke-dashoffset="888"/></svg>
    <div class="wrap">
      <div id="intro-k" class="lab k">${esc(T.intro.kicker)}</div>
      <div id="intro-t" class="big">${br(T.intro.title)}</div>
      <div id="intro-s" class="sub s2">${esc(T.intro.sub)}</div>
    </div>`;
  const js = `      tl.fromTo("#intro-path", { attr: { "stroke-dashoffset": 888 } }, { attr: { "stroke-dashoffset": 0 }, duration: 0.6, ease: "power2.inOut" }, 0);
      rise("#intro-k", 0.2, 0.45, 14); rise("#intro-t", 0.3, 0.6, 36); rise("#intro-s", 0.6);
      leave("#intro-line", ${f(d - 0.32)}); leave("#intro-k", ${f(d - 0.32)}); leave("#intro-t", ${f(d - 0.3)}); leave("#intro-s", ${f(d - 0.3)});`;
  return scene("intro", css, html, js);
}

function endScene() {
  const css = `.wrap { position: absolute; left: 96px; top: 330px; width: 888px; }
.big { font-weight: 900; font-size: 88px; line-height: 1.0; letter-spacing: -0.035em; }
.url { margin-top: 44px; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 34px; color: ${A}; }
.bar { margin-top: 14px; height: 3px; width: 640px; background: ${A}; transform-origin: 0 50%; }
.foot { margin-top: 56px; font-size: 28px; line-height: 1.35; color: #8C95A4; }`;
  const html = `    <div class="wrap">
      <div id="end-t" class="big">${br(T.end.title)}</div>
      <div id="end-u" class="url">${esc(T.end.url)}</div>
      <div id="end-bar" class="bar"></div>
      <div id="end-f" class="foot">${esc(T.end.foot)}</div>
    </div>`;
  const js = `      rise("#end-t", 0.1, 0.6, 36); rise("#end-u", 0.55);
      tl.fromTo("#end-bar", { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: "power2.inOut" }, 0.7);
      rise("#end-f", 1.0);`;
  return scene("end", css, html, js);
}

function frameScene() {
  const corner = (id, x, y, rot) => `    <svg id="frame-${id}" data-layout-ignore style="position:absolute;left:${x}px;top:${y}px;transform:rotate(${rot}deg)" width="34" height="34" viewBox="0 0 34 34"><path d="M1 33 V1 H33" stroke="rgba(255,255,255,0.32)" stroke-width="2" fill="none"/></svg>`;
  const counts = scenes.map(s => `      <span id="frame-c${s.n}" class="clip" data-start="${s.start}" data-duration="${s.duration}" data-track-index="2">${n2(s.n)} / ${n2(scenes.length)}</span>`).join("\n");
  const css = `.brand { position: absolute; left: 62px; top: 58px; display: flex; align-items: center; gap: 12px; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 20px; letter-spacing: 0.14em; text-transform: uppercase; color: #C9D0DB; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: ${A}; box-shadow: 0 0 14px ${A}; }
.count { position: absolute; right: 62px; top: 58px; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 20px; letter-spacing: 0.14em; color: #C9D0DB; }
.count span { position: absolute; right: 0; white-space: nowrap; }
.track { position: absolute; left: 62px; right: 62px; top: 1018px; height: 3px; background: rgba(255,255,255,0.12); }
.fill { position: absolute; inset: 0; background: ${A}; transform-origin: 0 50%; }`;
  const html = `${corner("tl", 24, 24, 0)}
${corner("tr", S - 58, 24, 90)}
${corner("br", S - 58, S - 58, 180)}
${corner("bl", 24, S - 58, 270)}
    <div id="frame-brand" class="brand" data-layout-ignore><div class="dot"></div><div>${esc(T.brand)}</div></div>
    <div id="frame-count" class="count" data-layout-ignore>
${counts}
    </div>
    <div id="frame-track" class="track"><div id="frame-fill" class="fill"></div></div>`;
  const js = `      tl.fromTo("#frame-fill", { scaleX: 0 }, { scaleX: 1, duration: ${TOTAL}, ease: "none" }, 0);
      tl.fromTo("#frame-brand", { opacity: 0 }, { opacity: 1, duration: 0.6, ease: "power2.out" }, 0.2);`;
  return scene("frame", css, html, js);
}

// ---- root -----------------------------------------------------------------------------------------------------
const host = (id, start, dur, z) => `      <div id="${id}" data-composition-id="${id}" data-composition-src="compositions/${id}.html" data-start="${start}" data-duration="${dur}" data-track-index="${z}" data-track-kind="graphics" data-width="${S}" data-height="${S}" style="z-index:${z}"></div>`;
const sfx = [];
scenes.forEach(s => {
  sfx.push({ id: `sfx-cap-${s.id}`, at: f(s.start + 0.25), src: T.sfx.caption, vol: T.sfx.volumeCaption });
  (s.clicks || []).forEach((c, i) => sfx.push({ id: `sfx-click-${s.id}-${i}`, at: f(s.start + c - s.mediaStart), src: T.sfx.click, vol: T.sfx.volumeClick }));
});
const audio = [
  `      <audio id="music" class="clip" src="${T.music.src}" data-start="0" data-duration="${TOTAL}" data-media-start="${T.music.start}" data-volume="${T.music.volume}" data-fade-in="0.4" data-fade-out="1.6" data-track-index="20"></audio>`,
  ...sfx.map((x, i) => `      <audio id="${x.id}" class="clip" src="${x.src}" data-start="${x.at}" data-duration="0.5" data-volume="${x.vol}" data-track-index="${21 + (i % 2)}"></audio>`),
].join("\n");

const index = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${S}, height=${S}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: ${S}px; height: ${S}px; overflow: hidden; background: #070B14; }
      #root { position: relative; width: 100%; height: 100%; }
      #ground { position: absolute; inset: 0; z-index: 0;
        background:
          radial-gradient(640px 520px at 78% 30%, ${A}2E, transparent 70%),
          radial-gradient(720px 620px at 12% 82%, rgba(46,140,170,0.22), transparent 70%),
          linear-gradient(180deg, #0B1322 0%, #070B14 100%); }
      #grid { position: absolute; inset: 0; z-index: 0; opacity: 0.35;
        background-image: linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.045) 1px, transparent 1px);
        background-size: 54px 54px; }
    </style>
  </head>
  <body>
    <!-- Generated by build.mjs from teaser.json. Edit those, then run: node build.mjs -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="${TOTAL}" data-width="${S}" data-height="${S}">
      <div id="ground" data-layout-ignore></div>
      <div id="grid" data-layout-ignore></div>
${host("intro", intro.start, intro.duration, 2)}
${scenes.map(s => host(s.id, s.start, s.duration, 2)).join("\n")}
${host("end", end.start, end.duration, 2)}
${host("frame", 0, TOTAL, 5)}
${audio}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({ paused: true });
    </script>
  </body>
</html>
`;

mkdirSync(new URL("./compositions/", import.meta.url), { recursive: true });
const out = (name, s) => writeFileSync(new URL(name, import.meta.url), s);
out("index.html", index);
out("compositions/intro.html", introScene());
scenes.forEach(s => out(`compositions/${s.id}.html`, s.numbers ? numbersScene(s) : clipScene(s)));
out("compositions/end.html", endScene());
out("compositions/frame.html", frameScene());
console.log(`built ${scenes.length + 3} compositions, ${TOTAL} s, ${sfx.length} sounds`);
