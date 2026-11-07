"""Build the HyperFrames film from timings.json (voice clock) and the real P001/P019 data.

Usage: python3 build.py   -> index.html, compositions/*.html, assets/audio/{bed.wav, voice/*.wav}
Every sentence, quote, span, score and number shown is copied from the pipeline output or eval/*.md.
"""
import html
import json
import pathlib
import re
import subprocess

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent
T = json.loads((HERE / "timings.json").read_text())
SC = {s["id"]: s for s in T["scenes"]}
TOTAL = T["total"]
PACKET = json.loads(sorted((ROOT / "data" / "packets_hard").glob("packet_*.json"))[0].read_text())
DOCS = {d["doc_id"]: d for d in PACKET["documents"]}
assert PACKET["packet_id"] == "P001"

INK, MUTED, LINE = "#1D1D1B", "#5D5D58", "#E2E0D8"
RED, REDBG, OK, OKBG, WARN, WARNBG, INFO, INFOBG = "#A4161A", "#FDE8E8", "#1F7A4D", "#E6F3EC", "#9A5B00", "#FDF0DC", "#2B5C9E", "#E7EEF9"
e = html.escape

BASE_CSS = f"""
#root {{ position: absolute; inset: 0; overflow: hidden; font-family: "Inter", sans-serif; color: {INK}; }}
.all {{ position: absolute; inset: 0; }}
.card {{ position: absolute; background: #FFFFFF; border: 1px solid {LINE}; border-radius: 14px;
  box-shadow: 0 18px 40px rgba(29,29,27,0.08); }}
.chip {{ display: inline-block; font-weight: 700; font-size: 28px; line-height: 1; padding: 9px 18px; border-radius: 999px; white-space: nowrap; }}
.bad {{ color: {RED}; background: {REDBG}; }} .ok {{ color: {OK}; background: {OKBG}; }}
.warn {{ color: {WARN}; background: {WARNBG}; }} .info {{ color: {INFO}; background: {INFOBG}; }}
.mono {{ font-family: "JetBrains Mono", monospace; font-variant-ligatures: none; font-feature-settings: "calt" 0, "liga" 0; }}
.muted {{ color: {MUTED}; }}
.hide {{ opacity: 0; }}
"""

JS_HELPERS = """
const arrive = (sel, t, from = { y: 28 }) => tl.fromTo(sel, { opacity: 0, ...from }, { opacity: 1, x: 0, y: 0, duration: 0.5, ease: "expo.out" }, t);
const blurIn = (sel, t, d = 0.2) => tl.fromTo(sel, { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: d, ease: "expo.out" }, t);
const leave = (sel, t) => tl.to(sel, { opacity: 0, filter: "blur(6px)", duration: 0.25, ease: "power3.in" }, t);
const box = (sel, t, c, bg) => tl.fromTo(sel, { boxShadow: "0 0 0 0px " + c, backgroundColor: "rgba(255,255,255,0)" }, { boxShadow: "0 0 0 4px " + c, backgroundColor: bg, duration: 0.3, ease: "power2.out" }, t);
const stamp = (sel, t) => { tl.set(sel, { opacity: 1 }, t); tl.fromTo(sel, { scale: 1.14 }, { scale: 1, duration: 0.18, ease: "power2.out" }, t); };
const cam = (sel, t, x, y, s, d = 0.8) => tl.to(sel, { x: x, y: y, scale: s, duration: d, ease: "power2.inOut" }, t);
const strike = (sel, t, d = 0.35) => tl.fromTo(sel, { scaleX: 0 }, { scaleX: 1, duration: d, ease: "power1.inOut", transformOrigin: "0% 50%" }, t);
const typeChars = (sel, t0, t1) => { const cs = gsap.utils.toArray(sel); const g = (t1 - t0) / cs.length; cs.forEach((c, i) => tl.set(c, { opacity: 1 }, t0 + i * g)); };
const count = (sel, t, a, b, d, fmt) => { const o = { v: a }; const el = document.querySelector(sel);
  tl.fromTo(o, { v: a }, { v: b, duration: d, ease: "power2.out", onUpdate: () => { el.textContent = fmt(Math.round(o.v)); } }, t); };
"""


def loc(scene: str, cue: str) -> float:
    s = SC[scene]
    return round(s["cues"][cue] - s["start"], 3)


def scene_file(sid: str, css: str, body: str, js: str) -> str:
    dur = SC[sid]["dur"] if sid in SC else TOTAL
    return f"""<template>
  <style>{BASE_CSS}{css}</style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
    <div id="{sid}-all" class="all clip" data-start="0" data-duration="{dur}" data-track-index="1">
{body}
    </div>
  </div>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});
{JS_HELPERS}
{js}
      window.__timelines["{sid}"] = tl;
    }})();
  </script>
</template>
"""


# ---------- record cards (real text, one div per line so a line can be boxed) ----------
CARD_X = {"D1": 70, "D2": 520, "D3": 970, "D4": 1420}
CARD_LABEL = {"D1": ("Clinic note", "Alexandria · 2024-08-15"), "D2": ("Discharge summary", "Cairo · 2025-01-11"),
              "D3": ("Pharmacy record", "Valencia · 2025-04-17"), "D4": ("GP letter · Spanish", "Valencia · 2025-12-25")}
CARD_CSS = f"""
.rec {{ top: 150px; width: 430px; padding: 22px 22px 18px; }}
.rec h3 {{ font-size: 30px; font-weight: 700; letter-spacing: -0.01em; }}
.rec .where {{ font-size: 24px; color: {MUTED}; margin: 4px 0 14px; }}
.rec .ln {{ font-size: 16.5px; line-height: 23px; white-space: pre-wrap; border-radius: 4px; min-height: 12px; padding: 0 3px; margin: 0 -3px; }}
.rec .gloss {{ font-size: 17px; color: {RED}; font-weight: 700; margin: 2px 0 4px; }}
"""


HIDE = " hide"


def record_card(prefix: str, doc: str, gloss: bool = False, hidden: bool = False) -> str:
    lines = DOCS[doc]["text"].split("\n")
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<div id="{prefix}-{doc}-l{i}" class="ln mono">{e(ln) if ln else "&#8203;"}</div>')
        if gloss and doc == "D4" and ln.startswith("Sin alergias"):
            out.append(f'<div id="{prefix}-gloss" class="gloss hide">= no known drug allergies</div>')
    kind, where = CARD_LABEL[doc]
    extra = HIDE if hidden else ""
    return (f'<div id="{prefix}-{doc}" class="card rec{extra}" style="left:{CARD_X[doc]}px">'
            f'<h3>{e(kind)}</h3><div class="where">{e(where)}</div>{"".join(out)}</div>')


def line_no(doc: str, starts: str) -> int:
    return next(i for i, ln in enumerate(DOCS[doc]["text"].split("\n")) if ln.startswith(starts))


# ---------- scenes ----------
def hook() -> str:
    s = "hook"
    gp, ph = line_no("D4", "Sin alergias"), line_no("D3", "Allergies:")
    body = f"""<div id="hk-cam" style="position:absolute;inset:0">
{''.join(record_card('hk', d, gloss=True, hidden=d != 'D4') for d in ['D1', 'D2', 'D3', 'D4'])}
</div>
<div id="hk-sheet" class="card hide" style="left:70px;top:700px;width:1780px;height:190px;padding:26px 34px">
  <div style="font-size:40px;font-weight:800;letter-spacing:-0.02em">Handoff</div>
  <div class="muted" style="font-size:30px;margin-top:6px">the summary the next doctor reads: both allergy statements have to be in it</div>
</div>"""
    # camera: GP card alone -> GP + pharmacy pair -> all four (scale 1)
    js = f"""
tl.set("#hk-cam", {{ transformOrigin: "0px 0px", x: -1819.5, y: -228, scale: 1.7 }}, 0);
box("#hk-D4-l{gp}", {loc(s, 'gp_box')}, "{RED}", "{REDBG}");
blurIn("#hk-gloss", {loc(s, 'gp_box') + 0.25});
cam("#hk-cam", {loc(s, 'pharm_in') - 0.1}, -1437, -228, 1.7, 0.9);
tl.fromTo("#hk-D3", {{ opacity: 0, x: 140 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out" }}, {loc(s, 'pharm_in')});
box("#hk-D3-l{ph}", {loc(s, 'pharm_box')}, "{RED}", "{REDBG}");
cam("#hk-cam", {loc(s, 'fan') - 0.2}, 0, 0, 1, 1.0);
tl.fromTo(["#hk-D2", "#hk-D1"], {{ opacity: 0, x: -160 }}, {{ opacity: 1, x: 0, duration: 0.6, ease: "expo.out", stagger: 0.12 }}, {loc(s, 'fan') + 0.3});
arrive("#hk-sheet", {loc(s, 'sheet')}, {{ y: 60 }});
"""
    return scene_file(s, CARD_CSS, body, js)


def protect() -> str:
    s = "protect"
    hits = {d: line_no(d, "Patient" if d != "D4" else "Paciente") for d in DOCS}
    scans = "".join(f'<div id="pr-scan-{d}" class="hide" style="position:absolute;left:{CARD_X[d]}px;top:150px;width:6px;height:520px;background:{OK};border-radius:3px"></div>' for d in DOCS)
    tags = "".join(f'<div id="pr-tag-{d}" class="chip ok hide" style="position:absolute;left:{CARD_X[d]}px;top:690px">allowed: synthetic code</div>' for d in DOCS)
    body = f"""{''.join(record_card('pr', d) for d in ['D1', 'D2', 'D3', 'D4'])}
{scans}{tags}
<div id="pr-pass" class="hide" style="position:absolute;left:70px;top:790px;display:flex;align-items:center;gap:22px">
  <span class="chip ok">Privacy gate passed</span><span style="font-size:34px">4 of 4 records: only the synthetic case code</span></div>"""
    js = f"const t0 = {loc(s, 'title') + 0.6};\n"
    for i, d in enumerate(["D1", "D2", "D3", "D4"]):
        js += (f'tl.set("#pr-scan-{d}", {{ opacity: 1 }}, t0 + {i * 0.95});'
               f'tl.fromTo("#pr-scan-{d}", {{ x: 0 }}, {{ x: 424, duration: 0.85, ease: "power1.inOut" }}, t0 + {i * 0.95});'
               f'tl.to("#pr-scan-{d}", {{ opacity: 0, duration: 0.1 }}, t0 + {i * 0.95 + 0.85});\n')
    for i, d in enumerate(["D1", "D2", "D3", "D4"]):
        js += f'box("#pr-{d}-l{hits[d]}", {loc(s, "hits") + i * 0.18}, "{OK}", "{OKBG}"); arrive("#pr-tag-{d}", {loc(s, "hits") + 0.1 + i * 0.18}, {{ y: -16 }});\n'
    js += f'arrive("#pr-pass", {loc(s, "hits") + 1.4});\n'
    return scene_file(s, CARD_CSS, body, js)


EXTRACTED = [  # (doc, line prefix, shown text, span or None) from build(packet)["extracted"]
    ("D3", "Allergies:", "sulfonamides (hives)", "[127, 147]"),
    ("D4", "Sin alergias", "Sin alergias medicamentosas conocidas.", "no-known-allergy statement"),
    ("D3", "- warfarin", "- warfarin 3mg OD as per INR", "[234, 263]"),
    ("D3", "- bisoprolol", "- bisoprolol 2.5mg OD", "[186, 208]"),
    ("D4", "- bisoprolol", "- bisoprolol 5 mg una vez al día", "[274, 307]"),
]


def extract() -> str:
    s = "extract"
    rows = ""
    for i, (doc, _, text, span) in enumerate(EXTRACTED):
        rows += (f'<div id="ex-r{i}" class="hide" style="position:absolute;left:70px;top:{676 + i * 50}px;display:flex;gap:26px;align-items:baseline">'
                 f'<span class="muted" style="width:330px;font-size:28px">{e(CARD_LABEL[doc][0])}</span>'
                 f'<span class="mono" style="width:920px;font-size:30px">{e(text)}</span>'
                 f'<span id="ex-s{i}" class="mono hide" style="font-size:28px;color:{INFO}">{e(span)}</span></div>')
    body = f"""{''.join(record_card('ex', d) for d in ['D1', 'D2', 'D3', 'D4'])}
{rows}"""
    js = ""
    for i, (doc, pre, _, _) in enumerate(EXTRACTED):
        t = loc(s, "lift_allergy") + i * 0.12 if i < 2 else loc(s, "lift_meds") + (i - 2) * 0.15
        js += f'box("#ex-{doc}-l{line_no(doc, pre)}", {t}, "{WARN}", "{WARNBG}"); arrive("#ex-r{i}", {t + 0.15}, {{ y: -36 }});\n'
    js += "".join(f'blurIn("#ex-s{i}", {loc(s, "offsets") + i * 0.1});' for i in range(len(EXTRACTED)))
    return scene_file(s, CARD_CSS, body, js)


RULE_ROWS = [  # item, chip class, chip text, four cells (D1..D4), from handoff labels and the site
    ("Allergy", "bad", "Allergy conflict", ["not mentioned", "not mentioned", "sulfonamides (hives)", "Sin alergias medicamentosas conocidas."]),
    ("Warfarin", "warn", "Missing from newest record", ["warfarin 3 mg OD as per INR", "warfarin 3 mg OD as per INR", "warfarin 3mg OD as per INR", "not listed"]),
    ("Bisoprolol", "warn", "Dose or timing differs", ["bisoprolol 2.5mg o.d.", "bisoprolol 2.5 mg o.d.", "bisoprolol 2.5mg OD", "bisoprolol 5 mg una vez al día"]),
]


def rules() -> str:
    s = "rules"
    colx = [520, 870, 1220, 1570]
    heads = "".join(f'<div style="position:absolute;left:{x}px;top:140px;width:330px;font-size:28px;line-height:34px">'
                    f'<b>{e(CARD_LABEL[d][0].replace(" · Spanish", ""))}</b><br><span class="muted">{e(CARD_LABEL[d][1].split(" · ")[1])}</span></div>'
                    for x, d in zip(colx, ["D1", "D2", "D3", "D4"]))
    rows = ""
    for r, (item, cls, chip, cells) in enumerate(RULE_ROWS):
        y = 240 + r * 190
        cs = "".join(f'<div id="ru-c{r}{k}" class="mono" style="position:absolute;left:{x - 10}px;top:{y + 8}px;width:340px;padding:8px 10px;border-radius:6px;font-size:28px;line-height:38px;{"color:" + MUTED + ";font-style:normal" if c in ("not mentioned", "not listed") else ""}">{e(c)}</div>'
                     for k, (x, c) in enumerate(zip(colx, cells)))
        rows += (f'<div id="ru-row{r}" class="card" style="left:70px;top:{y}px;width:1780px;height:170px"></div>'
                 f'<div style="position:absolute;left:100px;top:{y + 22}px;font-size:40px;font-weight:800">{e(item)}</div>'
                 f'<div id="ru-chip{r}" class="chip {cls} hide" style="position:absolute;left:100px;top:{y + 92}px">{e(chip)}</div>{cs}')
    body = f"""<div id="ru-cam" style="position:absolute;inset:0">{heads}{rows}</div>
<div id="ru-sign" class="hide" style="position:absolute;left:70px;top:820px;font-size:34px">
  <b>Physician-signed rules</b> <span class="muted">· no model decides a label</span></div>"""
    js = f'tl.set("#ru-cam", {{ transformOrigin: "0px 0px" }}, 0); arrive("#ru-cam", 0.05, {{ y: 30 }});\n'
    js += f'blurIn("#ru-sign", {loc(s, "title")});\n'
    for r in range(3):
        js += f'stamp("#ru-chip{r}", {loc(s, "chips") + 0.3 * r});\n'
    js += f'box("#ru-c13", {loc(s, "warfarin") + 0.6}, "{WARN}", "{WARNBG}");\n'
    js += f'tl.to(["#ru-row0", "#ru-row2"], {{ opacity: 0.35, duration: 0.4 }}, {loc(s, "warfarin") - 0.2});\n'
    return scene_file(s, "", body, js)


FILL_TEXT = ("Allergy conflict new: the pharmacy record of 2025-04-17 says 'sulfonamides (hives)' and the GP letter of "
             "2025-12-25 says 'Sin alergias medicamentosas conocidas.")  # summary.removed[0]["sentence"], verbatim
SHEET_CSS = f"""
.sheet {{ left: 160px; top: 140px; width: 1600px; height: 470px; padding: 34px 48px; }}
.sheet h2 {{ font-size: 40px; font-weight: 800; letter-spacing: -0.02em; }}
.sheet .who {{ font-size: 28px; color: {MUTED}; margin-top: 4px; }}
.sent {{ position: absolute; left: 48px; top: 150px; width: 1500px; font-size: 42px; line-height: 60px; }}
.q {{ font-family: "JetBrains Mono", monospace; font-size: 36px; }}
.mini {{ top: 650px; width: 760px; height: 190px; padding: 22px 28px; }}
.mini h4 {{ font-size: 28px; font-weight: 700; }}
.mini .mono {{ font-size: 30px; margin-top: 18px; padding: 4px 6px; margin-left: -6px; border-radius: 6px; display: inline-block; }}
"""


def chars(text: str, cls: str = "ch") -> str:
    return "".join(f'<span class="{cls}" style="opacity:0">{e(c)}</span>' for c in text)


def fill() -> str:
    s = "fill"
    body = f"""<div id="fi-sheet" class="card sheet"><h2>Written handoff</h2><div class="who">draft by Clocked Fill</div>
  <div id="fi-sent" class="sent">{chars(FILL_TEXT, "fi-ch")}</div></div>"""
    js = f'arrive("#fi-sheet", 0.05, {{ y: 40 }});\ntypeChars("#fi-sent .fi-ch", {loc(s, "title") + 0.5}, {loc(s, "type") + 1.0});\n'
    return scene_file(s, SHEET_CSS, body, js)


def mini(prefix: str, which: str, x: int) -> str:
    label, text = ("Pharmacy record · 2025-04-17", "Allergies: sulfonamides (hives)") if which == "ph" else \
        ("GP letter · 2025-12-25 · Spanish", "Sin alergias medicamentosas conocidas.")
    return f'<div id="{prefix}-{which}" class="card mini" style="left:{x}px"><h4>{e(label)}</h4><div id="{prefix}-{which}-q" class="mono">{e(text)}</div></div>'


def verify() -> str:
    s = "verify"
    # the removed fold-out, cropped from the real site capture (y 690..940 of 978 px)
    body = f"""<div id="ve-sheet" class="card sheet"><h2>Written handoff</h2><div class="who">draft by Clocked Fill</div>
  <div id="ve-sent" class="sent">{e(FILL_TEXT)}
    <div id="ve-band" class="hide" style="position:absolute;left:-12px;top:0;width:60px;height:180px;background:rgba(43,92,158,0.12);border-radius:8px"></div>
    {''.join(f'<div id="ve-x{i}" style="position:absolute;left:0;top:{28 + 60 * i}px;width:{[1490, 1480, 1060][i]}px;height:5px;background:{RED};transform:scaleX(0)"></div>' for i in range(3))}
  </div>
  <div id="ve-stamp" class="hide" style="position:absolute;right:46px;top:34px;border:4px solid {RED};color:{RED};border-radius:12px;padding:10px 20px;font-size:34px;font-weight:900;transform:rotate(-3deg)">Verify: contradicted · 0.40</div>
</div>
{mini('ve', 'ph', 160)}{mini('ve', 'gp', 1000)}
<div id="ve-real" class="hide" data-layout-allow-overflow style="position:absolute;left:160px;top:650px;width:1600px;height:275px;overflow:hidden;border-radius:14px">
  <img src="assets/site/p001_handoff_removed.png" style="position:absolute;left:0;top:-758px;width:1600px" alt="Removed sentence on the patient page"></div>"""
    js = f"""
arrive("#ve-ph", {loc(s, 'title') + 0.2}, {{ y: 50 }}); arrive("#ve-gp", {loc(s, 'title') + 0.35}, {{ y: 50 }});
tl.set("#ve-band", {{ opacity: 1 }}, {loc(s, 'scan')});
tl.fromTo("#ve-band", {{ x: 0 }}, {{ x: 1460, duration: 1.6, ease: "power1.inOut" }}, {loc(s, 'scan')});
tl.to("#ve-band", {{ opacity: 0, duration: 0.15 }}, {loc(s, 'scan') + 1.6});
box("#ve-ph-q", {loc(s, 'scan') + 0.5}, "{RED}", "{REDBG}"); box("#ve-gp-q", {loc(s, 'scan') + 1.0}, "{RED}", "{REDBG}");
stamp("#ve-stamp", {loc(s, 'stamp')});
strike("#ve-x0", {loc(s, 'remove')}); strike("#ve-x1", {loc(s, 'remove') + 0.25}); strike("#ve-x2", {loc(s, 'remove') + 0.5});
tl.to("#ve-sent", {{ opacity: 0.35, duration: 0.3 }}, {loc(s, 'remove') + 0.9});
leave(["#ve-ph", "#ve-gp"], {loc(s, 'remove') + 0.9});
arrive("#ve-real", {loc(s, 'remove') + 1.1}, {{ y: 60 }});
"""
    return scene_file(s, SHEET_CSS, body, js)


PART1, PART2 = "The pharmacy record of 2025-04-17 says 'sulfonamides (hives)'.", "The GP letter of 2025-12-25 says 'Sin alergias medicamentosas conocidas.'."


def part(text: str) -> str:
    i, j = text.index("'"), text.rindex("'")
    return f'{e(text[:i])}<span class="q">{e(text[i:j + 1])}</span>{e(text[j + 1:])}'


def rebuild() -> str:
    s = "rebuild"
    body = f"""<div id="rb-stage" style="position:absolute;inset:0">
<div id="rb-sheet" class="card sheet"><h2>Written handoff</h2><div class="who">rebuilt by the rules from exact quotes</div>
  <div class="sent" style="top:140px">
    <div id="rb-head" class="hide" style="font-weight:800">Allergy conflict:</div>
    <div id="rb-p1" class="hide" style="position:relative;padding:4px 8px;margin-left:-8px;border-radius:8px">{part(PART1)} <span id="rb-s1" class="chip ok hide" style="margin-left:14px;vertical-align:4px">Verify: supported</span></div>
    <div id="rb-p2" class="hide" style="position:relative;padding:4px 8px;margin-left:-8px;border-radius:8px">{part(PART2)} <span id="rb-s2" class="chip ok hide" style="margin-left:14px;vertical-align:4px">Verify: supported</span></div>
  </div>
</div>
{mini('rb', 'ph', 160)}{mini('rb', 'gp', 1000)}
</div>
<div id="rb-real" class="hide" style="position:absolute;left:160px;top:130px;width:1600px">
  <div class="muted" style="font-size:30px;margin-bottom:16px">On the patient's page (synthetic patient P001)</div>
  <img src="assets/site/p001_handoff_top.png" style="width:1600px;display:block;border-radius:12px;background:#fff;border:1px solid {LINE}" alt="Final allergy sentence">
  <img src="assets/site/p001_banner.png" style="width:1400px;display:block;margin-top:34px;border-radius:12px" alt="Allergy conflict banner">
</div>"""
    q = loc(s, "quotes")
    js = f"""
tl.set(["#rb-ph", "#rb-gp"], {{ opacity: 1 }}, 0);
blurIn("#rb-head", {q});
tl.fromTo("#rb-p1", {{ opacity: 0, x: -150, y: 420 }}, {{ opacity: 1, x: 0, y: 0, duration: 0.7, ease: "power3.out" }}, {q + 0.3});
tl.fromTo("#rb-p2", {{ opacity: 0, x: 600, y: 360 }}, {{ opacity: 1, x: 0, y: 0, duration: 0.7, ease: "power3.out" }}, {q + 0.9});
box("#rb-ph-q", {q + 0.2}, "{OK}", "{OKBG}"); box("#rb-gp-q", {q + 0.8}, "{OK}", "{OKBG}");
box("#rb-p1", {loc(s, 'check')}, "{INFO}", "{INFOBG}"); box("#rb-p2", {loc(s, 'check') + 0.9}, "{INFO}", "{INFOBG}");
tl.to(["#rb-p1", "#rb-p2"], {{ boxShadow: "0 0 0 0px {OK}", backgroundColor: "rgba(255,255,255,0)", duration: 0.25 }}, {loc(s, 'stamps') - 0.1});
stamp("#rb-s1", {loc(s, 'stamps')}); stamp("#rb-s2", {loc(s, 'stamps') + 0.3});
tl.to("#rb-stage", {{ opacity: 0, scale: 0.94, filter: "blur(8px)", duration: 0.35, ease: "power3.in" }}, {loc(s, 'realcard') - 0.2});
arrive("#rb-real", {loc(s, 'realcard') + 0.1}, {{ y: 40 }});
"""
    return scene_file(s, SHEET_CSS, body, js)


METFORMIN = [("D1", "metformin 500 mg bd"), ("D2", "metformin 500mg bd"), ("D3", "metformin 500 mg b.i.d."), ("D4", "metformina 500 mg cada 12 horas")]


def quiet() -> str:
    s = "quiet"
    rows = "".join(
        f'<div id="qu-r{i}" class="hide" style="position:absolute;left:120px;top:{250 + i * 125}px">'
        f'<div class="muted" style="font-size:28px">{e(CARD_LABEL[d][0])} · {e(CARD_LABEL[d][1].split(" · ")[1])}</div>'
        f'<div class="mono" style="font-size:40px;margin-top:4px">{e(t)}</div></div>'
        f'<div id="qu-n{i}" class="mono hide" style="position:absolute;left:1060px;top:{286 + i * 125}px;font-size:40px;color:{OK}">→ 500 mg | 2/day</div>'
        for i, (d, t) in enumerate(METFORMIN))
    body = f"""<div id="qu-h" class="hide" style="position:absolute;left:120px;top:140px;font-size:56px;font-weight:900;letter-spacing:-0.02em">Metformin</div>
{rows}
<div id="qu-chip" class="hide" style="position:absolute;left:1060px;top:800px;display:flex;gap:20px;align-items:center">
  <span class="chip ok">Same in all records</span><span style="font-size:34px">no flag</span></div>"""
    js = 'blurIn("#qu-h", 0.3);\n'
    js += "".join(f'arrive("#qu-r{i}", {0.9 + i * 0.35}, {{ x: -40, y: 0 }});' for i in range(4))
    js += "".join(f'arrive("#qu-n{i}", {loc(s, "collapse") - 0.4 + i * 0.12}, {{ x: -60, y: 0 }});' for i in range(4))
    js += f'stamp("#qu-chip", {loc(s, "collapse") + 0.6});\n'
    return scene_file(s, "", body, js)


def compare() -> str:
    s = "compare"
    body = f"""<div id="co-real" class="hide" style="position:absolute;left:160px;top:140px;width:1600px">
  <div class="muted" style="font-size:30px;margin-bottom:16px">Independent cross-checks on the patient's page (P001)</div>
  <img src="assets/site/p001_crosschecks.png" style="width:1600px;display:block;border-radius:12px" alt="Cross-checks panel"></div>
<div id="co-a" class="hide" style="position:absolute;left:160px;top:610px;width:760px">
  <div id="co-n" style="font-size:120px;font-weight:900;letter-spacing:-0.03em;font-variant-numeric:tabular-nums">0 / 39</div>
  <div style="font-size:32px;line-height:42px">rule-found conflicts that Compare also flagged, across 20 synthetic patients</div></div>
<div id="co-b" class="hide" style="position:absolute;left:1000px;top:610px;width:760px">
  <div style="font-size:120px;font-weight:900;letter-spacing:-0.03em">0</div>
  <div style="font-size:32px;line-height:42px">conflicts Compare found that no rule explained</div></div>"""
    js = f"""arrive("#co-real", {loc(s, 'title') - 0.3}, {{ y: 40 }});
arrive("#co-a", {loc(s, 'count') - 0.5}); count("#co-n", {loc(s, 'count') - 0.3}, 0, 25, 1.3, v => v + " / 39");
arrive("#co-b", {loc(s, 'zero')});
"""
    return scene_file(s, "", body, js)


def absence() -> str:
    s = "absence"
    sc = 1600 / 1456  # crop of the real P019 written-handoff capture, original y 30..372
    def bx(y0, y1): return f"left:{160 + 22 * sc:.0f}px;top:{230 + (y0 - 30) * sc:.0f}px;width:{1410 * sc:.0f}px;height:{(y1 - y0) * sc:.0f}px"
    body = f"""<div id="ab-tag" class="hide" style="position:absolute;left:160px;top:130px;font-size:34px"><b>Another synthetic patient</b> <span class="muted">· P019</span></div>
<div id="ab-real" class="hide" data-layout-allow-overflow style="position:absolute;left:160px;top:230px;width:1600px;height:{342 * sc:.0f}px;overflow:hidden;border-radius:14px;border:1px solid {LINE};background:#fff">
  <img src="assets/site/p019_handoff.png" style="position:absolute;left:0;top:{-30 * sc:.0f}px;width:1600px" alt="P019 written handoff"></div>
<div id="ab-b2" style="position:absolute;{bx(160, 358)};border-radius:10px;box-shadow:0 0 0 0px {INFO}"></div>
<div id="ab-b1" style="position:absolute;{bx(48, 136)};border-radius:10px;box-shadow:0 0 0 0px {INFO}"></div>
<div id="ab-note" class="hide" style="position:absolute;left:160px;top:640px;width:1600px;font-size:34px;line-height:46px">
  Verify checks what is written. <b>An absence is found by comparing records</b>, and the sentence says so.</div>"""
    js = f"""blurIn("#ab-tag", 0.1); arrive("#ab-real", 0.2, {{ y: 40 }});
tl.fromTo("#ab-b2", {{ boxShadow: "0 0 0 0px {INFO}" }}, {{ boxShadow: "0 0 0 5px {INFO}", duration: 0.3 }}, {loc(s, 'lisinopril')});
arrive("#ab-note", {loc(s, 'lisinopril') + 0.8});
tl.to("#ab-b2", {{ boxShadow: "0 0 0 0px {INFO}", duration: 0.2 }}, {loc(s, 'unknown') - 0.2});
tl.fromTo("#ab-b1", {{ boxShadow: "0 0 0 0px {INFO}" }}, {{ boxShadow: "0 0 0 5px {INFO}", duration: 0.3 }}, {loc(s, 'unknown')});
"""
    return scene_file(s, "", body, js)


def numbers() -> str:
    s = "numbers"
    big = "font-size:112px;font-weight:900;letter-spacing:-0.03em;font-variant-numeric:tabular-nums;line-height:1"
    lab = "font-size:36px;line-height:44px"
    body = f"""<div id="nu-h" class="hide muted" style="position:absolute;left:120px;top:90px;font-size:36px;font-weight:700">20 synthetic patients · shorthand and Spanish records</div>
<div id="nu-r0" class="hide" style="position:absolute;left:120px;top:180px;display:flex;align-items:center;gap:40px">
  <div id="nu-n0" style="{big};width:560px;color:{MUTED}">54 / 100</div>
  <div id="nu-l0" style="{lab}">medication labels correct<br><span class="muted">before normalisation</span></div></div>
<div id="nu-r1" class="hide" style="position:absolute;left:120px;top:350px;display:flex;align-items:center;gap:40px">
  <div style="{big};width:560px">5 / 5</div><div style="{lab}">allergy conflicts flagged</div></div>
<div id="nu-r2" class="hide" style="position:absolute;left:120px;top:520px;display:flex;align-items:center;gap:40px">
  <div style="{big};width:560px">70 / 70</div><div style="{lab};width:420px">discrepancies named in the handoff</div></div>
<div id="nu-r2b" class="hide" style="position:absolute;left:1150px;top:520px;display:flex;align-items:center;gap:30px">
  <div style="{big};color:{MUTED}">55 / 70</div><div style="{lab};width:260px" class="muted">Fill and Verify alone</div></div>
<div id="nu-r3" class="hide" style="position:absolute;left:120px;top:690px;display:flex;align-items:center;gap:40px">
  <div style="{big};width:560px">0</div><div style="{lab}">invented medicines</div></div>"""
    n100 = loc(s, "n100")
    js = f"""blurIn("#nu-h", 0.2);
arrive("#nu-r0", {loc(s, 'n54') - 0.2});
tl.to("#nu-n0", {{ color: "{INK}", duration: 0.3 }}, {n100 - 0.5});
count("#nu-n0", {n100 - 0.5}, 54, 100, 0.8, v => v + " / 100");
tl.set("#nu-l0", {{ innerHTML: "medication labels correct<br><span class='muted'>54 / 100 before normalisation</span>" }}, {n100 + 0.3});
arrive("#nu-r1", {loc(s, 'n5') - 0.2}); arrive("#nu-r2", {loc(s, 'n70') - 0.2});
arrive("#nu-r2b", {loc(s, 'n55') - 0.2}); arrive("#nu-r3", {loc(s, 'n0') - 0.2});
"""
    return scene_file(s, "", body, js)


def end() -> str:
    s = "end"
    body = f"""<div id="en-line" class="hide" style="position:absolute;left:160px;top:250px;width:1500px;font-size:80px;font-weight:900;letter-spacing:-0.025em;line-height:92px">
  Every sentence verified, or labelled for what it is.</div>
<div id="en-meta" class="hide" style="position:absolute;left:160px;top:560px;width:1600px">
  <div class="mono" style="font-size:40px">github.com/DrAhmed7887/hack-clocked</div>
  <div style="font-size:32px;margin-top:22px">Built with Clocked Protect · Extract · Fill · Verify · Compare</div>
  <div class="muted" style="font-size:30px;margin-top:14px">Synthetic records only. Decision support for clinicians, not a prescription.</div></div>"""
    js = f'tl.fromTo("#en-line", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.3, ease: "expo.out" }}, {loc(s, "line")});\narrive("#en-meta", {loc(s, "line") + 1.4});\n'
    return scene_file(s, "", body, js)


# ---------- overlays: endpoint rail, captions ----------
RAIL = ["Protect", "Extract", "Rules", "Fill", "Verify", "Compare"]
RAIL_ON = {"protect": ["Protect"], "extract": ["Extract"], "rules": ["Rules"], "fill": ["Fill"], "verify": ["Verify"],
           "rebuild": ["Rules", "Verify"], "quiet": ["Rules"], "compare": ["Compare"]}


def rail() -> tuple:
    start, end_ = SC["protect"]["start"], SC["absence"]["start"]
    items = "".join(f'<span id="ra-{w}" style="font-size:30px;font-weight:700;color:#8E8C85;padding-bottom:6px;border-bottom:4px solid rgba(29,29,27,0)">{w}</span>' for w in RAIL)
    body = f'<div id="ra-bar" style="position:absolute;left:70px;top:44px;display:flex;gap:40px">{items}</div>'
    js = 'tl.fromTo("#ra-bar", { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0.1);\n'
    for sid, on in RAIL_ON.items():
        t = round(SC[sid]["start"] - start, 3)
        for w in RAIL:
            lit = w in on
            js += (f'tl.set("#ra-{w}", {{ color: "{INK if lit else "#8E8C85"}", borderBottomColor: "{"rgba(29,29,27,1)" if lit else "rgba(29,29,27,0)"}" }}, {max(t, 0.001)});')
        js += "\n"
    html_ = f"""<template>
  <style>#root {{ position: absolute; inset: 0; font-family: "Inter", sans-serif; }}</style>
  <div id="root" data-composition-id="rail" data-width="1920" data-height="1080">
    <div id="rail-all" class="clip" data-start="0" data-duration="{round(end_ - start, 3)}" data-track-index="1">{body}</div>
  </div>
  <script>(function () {{ const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["rail"] = tl; }})();</script>
</template>
"""
    return html_, start, round(end_ - start, 3)


def caption_groups() -> list:
    groups = []
    for sc in T["scenes"]:
        cur = []
        for w in sc["words"]:
            cur.append(w)
            if len(cur) >= 6 or re.search(r"[.:;]$", w["text"]) or (w["text"].endswith(",") and len(cur) >= 2):
                groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
    out = []
    for g in groups:
        out.append({"text": " ".join(w["text"] for w in g), "start": g[0]["start"] - 0.05, "end": g[-1]["end"] + 0.15})
    for a, b in zip(out, out[1:]):
        a["end"] = min(a["end"], b["start"] - 0.01)
    return out


def captions() -> str:
    gs = caption_groups()
    body = "".join(f'<div id="cap-{i}" class="cg"><span>{e(g["text"])}</span></div>' for i, g in enumerate(gs))
    js = ""
    for i, g in enumerate(gs):
        js += (f'tl.fromTo("#cap-{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.08 }}, {g["start"]:.3f});'
               f'tl.to("#cap-{i}", {{ opacity: 0, duration: 0.08 }}, {g["end"] - 0.08:.3f});'
               f'tl.set("#cap-{i}", {{ opacity: 0, visibility: "hidden" }}, {g["end"]:.3f});\n')
    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; font-family: "Inter", sans-serif; }}
    .cg {{ position: absolute; left: 0; right: 0; bottom: 64px; text-align: center; opacity: 0; }}
    .cg span {{ display: inline-block; background: rgba(29,29,27,0.86); color: #fff; font-size: 40px; font-weight: 700;
      line-height: 54px; padding: 8px 22px; border-radius: 10px; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
    <div id="captions-all" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1" data-layout-allow-caption-zone>{body}</div>
  </div>
  <script>(function () {{ const tl = gsap.timeline({{ paused: true }});
{js}
window.__timelines["captions"] = tl; }})();</script>
</template>
"""


# ---------- audio ----------
SFX = [  # (file, scene, cue or None, offset, volume)
    ("whoosh_a", "hook", "pharm_in", -0.05, 0.45), ("whoosh_b", "hook", "fan", 0.25, 0.4), ("whoosh_a", "hook", "sheet", -0.05, 0.35),
    ("scan", "protect", "title", 0.6, 0.3), ("pop", "protect", "hits", 0.0, 0.45),
    ("tick_a", "extract", "lift_allergy", 0.1, 0.5), ("tick_b", "extract", "lift_meds", 0.1, 0.5),
    ("pop", "rules", "chips", 0.0, 0.45), ("pop", "rules", "chips", 0.3, 0.4), ("pop", "rules", "chips", 0.6, 0.45),
    ("whoosh_b", "rules", "warfarin", -0.2, 0.3),
    ("scan", "verify", "scan", 0.0, 0.3), ("stamp", "verify", "stamp", 0.03, 0.8),
    ("whoosh_a", "rebuild", "quotes", 0.3, 0.35), ("whoosh_b", "rebuild", "quotes", 0.9, 0.35),
    ("pop", "rebuild", "stamps", 0.03, 0.5), ("pop", "rebuild", "stamps", 0.33, 0.45), ("whoosh_a", "rebuild", "realcard", -0.2, 0.35),
    ("pop", "quiet", "collapse", 0.63, 0.45), ("pop", "compare", "count", 1.0, 0.45), ("pop", "compare", "zero", 0.03, 0.45),
    ("pop", "numbers", "n100", 0.3, 0.4), ("pop", "numbers", "n5", -0.15, 0.4), ("pop", "numbers", "n70", -0.15, 0.4), ("pop", "numbers", "n0", -0.15, 0.4),
]


def run(args: list) -> None:
    subprocess.run(args, check=True)


def prep_audio() -> None:
    vdir = HERE / "assets" / "audio" / "voice"
    for sc in T["scenes"]:
        src, dst = vdir / f"{sc['id']}.mp3", vdir / f"{sc['id']}.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "48000", str(dst)])
    # music bed: -16 LUFS, then 0.14 under the voice, dipped at the deletion, a little up for the numbers, faded out
    dip0, dip1 = SC["verify"]["cues"]["stamp"] - 0.4, SC["verify"]["cues"]["remove"] + 1.6
    nums = SC["numbers"]["start"]
    vol = (f"if(lt(t,{dip0}),0.14,if(lt(t,{dip0 + 0.4}),0.14-0.10*(t-{dip0})/0.4,if(lt(t,{dip1}),0.04,"
           f"if(lt(t,{dip1 + 0.8}),0.04+0.10*(t-{dip1})/0.8,if(lt(t,{nums}),0.14,0.17)))))")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(HERE / "assets/audio/raw/music.mp3"), "-af",
         f"loudnorm=I=-16:TP=-1.5:LRA=11,volume='{vol}':eval=frame,apad,afade=t=out:st={TOTAL - 3}:d=3,atrim=0:{TOTAL}",
         "-ar", "48000", str(HERE / "assets/audio/bed.wav")])


def media_len(path: pathlib.Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return round(float(out) - 0.005, 3)


def audio_tags() -> str:
    tags = [f'<audio id="bed" class="clip" src="assets/audio/bed.wav" data-start="0" data-duration="{media_len(HERE / "assets/audio/bed.wav")}" data-track-index="20" data-volume="1"></audio>']
    for sc in T["scenes"]:
        tags.append(f'<audio id="vo-{sc["id"]}" class="clip" src="assets/audio/voice/{sc["id"]}.wav" data-start="{sc["voice_at"]}" '
                    f'data-duration="{media_len(HERE / "assets/audio/voice" / (sc["id"] + ".wav"))}" data-track-index="21" data-volume="1"></audio>')
    for i, (f, sid, cue, off, v) in enumerate(SFX):
        t = round(SC[sid]["cues"][cue] + off, 3)
        tags.append(f'<audio id="sfx-{i}" class="clip" src="assets/audio/raw/sfx_{f}.mp3" data-start="{t}" data-duration="{media_len(HERE / "assets/audio/raw" / ("sfx_" + f + ".mp3"))}" '
                    f'data-track-index="{22 + i % 3}" data-volume="{v}"></audio>')
    return "\n      ".join(tags)


def main() -> None:
    comp = HERE / "compositions"
    comp.mkdir(exist_ok=True)
    builders = {"hook": hook, "protect": protect, "extract": extract, "rules": rules, "fill": fill, "verify": verify,
                "rebuild": rebuild, "quiet": quiet, "compare": compare, "absence": absence, "numbers": numbers, "end": end}
    hosts = []
    for k, (sid, fn) in enumerate(builders.items()):
        (comp / f"{sid}.html").write_text(fn())
        sc = SC[sid]
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{sc["start"]}" '
                     f'data-duration="{sc["dur"]}" data-track-index="{1 + k % 2}" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 2"></div>')
    rail_html, rs, rd = rail()
    (comp / "rail.html").write_text(rail_html)
    (comp / "captions.html").write_text(captions())
    hosts.append(f'<div id="rail" data-composition-id="rail" data-composition-src="compositions/rail.html" data-start="{rs}" data-duration="{rd}" '
                 f'data-track-index="3" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index: 3"></div>')
    hosts.append(f'<div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="0" '
                 f'data-duration="{TOTAL}" data-track-index="4" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index: 4"></div>')
    prep_audio()
    nl = "\n      "
    (HERE / "index.html").write_text(f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #F6F5F1; }}
      #root {{ width: 100%; height: 100%; position: relative; }}
      #ground {{ position: absolute; inset: 0; background: #F6F5F1; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="ground" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="0" style="z-index: 0"></div>
      {nl.join(hosts)}
      {audio_tags()}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
    print("built", len(builders), "scenes,", TOTAL, "s")


if __name__ == "__main__":
    main()
