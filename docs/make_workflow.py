"""Workflow diagram (landscape 1600x900 and LinkedIn 4:5 1080x1350) as SVG, rendered to PNG with headless Chrome.

Every step maps to real code: src/crosscheck.py (privacy_gate, compare_check), src/handoff.py (extract + label),
src/normalize.py, src/summary.py (Fill, Verify, R7a/R7b). The example line in each card is synthetic patient P001's
real output. Usage: python3 docs/make_workflow.py
"""
import html
import pathlib
import subprocess

HERE = pathlib.Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BG, CARD, INK, MUTED, LINE = "#F6F5F1", "#FFFFFF", "#1D1D1B", "#5D5D58", "#E2E0D8"
OK, OKBG, AMBER, AMBERBG = "#1F7A4D", "#E6F3EC", "#9A5B00", "#FDF0DC"
FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "Menlo, 'SF Mono', Consolas, monospace"

# (tag, tag style, title, body, example from P001)
STEPS = [
    ("INPUT", "plain", "4 records, 2 languages",
     "Clinic note (Alexandria), discharge summary (Cairo), pharmacy record and Spanish GP letter (Valencia).",
     "synthetic patient P001"),
    ("CLOCKED PROTECT · /pii", "clocked", "Privacy gate",
     "Scans every record for names, contact details, birth dates and IDs. Any other hit stops the run.",
     "found only: synthetic case P001"),
    ("CLOCKED EXTRACT", "clocked", "Copy facts word for word",
     "Allergies, problems and each medication line, with exact character positions.",
     "'sulfonamides (hives)' [127, 147]"),
    ("PHYSICIAN-SIGNED RULES", "rules", "Label every fact",
     "Normalise shorthand and Spanish, then label each fact: same, dose differs, missing from newest, new, stopped, allergy conflict. No model decides.",
     "→ Allergy conflict"),
    ("CLOCKED FILL", "clocked", "Draft the handoff",
     "One sentence per discrepancy, quoting the records.",
     "draft: 'Allergy conflict new: …'"),
    ("CLOCKED VERIFY · /grounding", "clocked", "Check every sentence",
     "Unsupported sentences are removed and shown. Conflicts are rebuilt from exact quotes, each verified alone; absences come from comparing records.",
     "contradicted 0.40 → rebuilt, 2/2 supported"),
    ("CLOCKED COMPARE", "clocked", "Independent cross-check",
     "Runs on the raw records. Any conflict no rule explains is shown to the clinician.",
     "also flagged: allergy, bisoprolol"),
    ("FOR THE RECEIVING CLINICIAN", "out", "Evidence-linked handoff",
     "Allergy alert first. Each sentence shows how it was checked, each fact is quoted, and conflicts are never resolved for the clinician.",
     "20 patients: 70/70 named, 0 invented medicines"),
]


SHORT = [  # one-line bodies for the 4:5 phone version
    "Clinic note, discharge summary, pharmacy record, Spanish GP letter.",
    "Any real name or ID found: the run stops.",
    "Each fact copied with its exact position.",
    "Same, dose differs, missing, stopped, allergy conflict.",
    "One sentence per discrepancy.",
    "Unsupported sentences removed; conflicts rebuilt from exact quotes.",
    "Runs on raw records; unexplained conflicts shown.",
    "Allergy first; every fact quoted; never resolved for you.",
]


def wrap(text: str, size: float, width: float, mono: bool = False) -> list:
    per = width / (size * (0.6 if mono else 0.52))
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > per:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + [cur] if cur else lines


def card(i: int, x: float, y: float, w: float, h: float, s: dict) -> str:
    tag, kind, title, body, ex = STEPS[i]
    body = SHORT[i] if s.get("short") else body
    pad = s["pad"]
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{OKBG if kind == "out" else CARD}" '
           f'stroke="{OK if kind == "out" else LINE}" stroke-width="{2 if kind == "out" else 1.5}"/>']
    # tag chip
    tag_fill, tag_ink = {"clocked": (INK, "#FFFFFF"), "rules": (AMBERBG, AMBER), "out": (OK, "#FFFFFF"),
                         "plain": ("#ECEAE3", MUTED)}[kind]
    tw = len(tag) * s["tag"] * 0.74 + 24
    out.append(f'<rect x="{x + pad}" y="{y + pad}" width="{tw}" height="{s["tag"] + 16}" rx="{(s["tag"] + 16) / 2}" fill="{tag_fill}"/>')
    out.append(f'<text x="{x + pad + 12}" y="{y + pad + s["tag"] + 3}" font-size="{s["tag"]}" font-weight="700" '
               f'letter-spacing="0.5" fill="{tag_ink}">{html.escape(tag)}</text>')
    ty = y + pad + s["tag"] + 16 + s["title"] + 14
    out.append(f'<text x="{x + pad}" y="{ty}" font-size="{s["title"]}" font-weight="800" fill="{INK}">{html.escape(title)}</text>')
    by = ty + 10
    for ln in wrap(body, s["body"], w - 2 * pad):
        by += s["body"] * 1.32
        out.append(f'<text x="{x + pad}" y="{by}" font-size="{s["body"]}" fill="{INK}">{html.escape(ln)}</text>')
    # example strip at the bottom
    exl = wrap(ex, s["ex"], w - 2 * pad - 24)
    eh = len(exl) * s["ex"] * 1.3 + 16
    ey = y + h - pad - eh
    out.append(f'<rect x="{x + pad}" y="{ey}" width="{w - 2 * pad}" height="{eh}" rx="8" fill="{BG}"/>')
    for k, ln in enumerate(exl):
        out.append(f'<text x="{x + pad + 12}" y="{ey + 8 + s["ex"] * (1.3 * k + 1) - 2}" font-size="{s["ex"]}" '
                   f'font-weight="600" fill="{OK if kind == "out" else MUTED}">{html.escape(ln)}</text>')
    return "\n".join(out)


def needed(i: int, w: float, s: dict) -> float:
    tag, kind, title, body, ex = STEPS[i]
    body = SHORT[i] if s.get("short") else body
    pad = s["pad"]
    return (pad + s["tag"] + 16 + s["title"] + 24 + len(wrap(body, s["body"], w - 2 * pad)) * s["body"] * 1.32
            + 18 + len(wrap(ex, s["ex"], w - 2 * pad - 24)) * s["ex"] * 1.3 + 16 + pad)


def arrow(x1, y1, x2, y2) -> str:
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="3" '
            f'marker-end="url(#ah)" stroke-linecap="round"/>')


def svg(W: int, H: int, cols: int, s: dict, head: dict) -> str:
    rows = (len(STEPS) + cols - 1) // cols
    gx, gy, mx = s["gx"], s["gy"], s["mx"]
    cw = (W - 2 * mx - (cols - 1) * gx) / cols
    top = head["top"]
    ch = (H - top - s["foot"] - (rows - 1) * gy) / rows
    need = max(needed(i, cw, s) for i in range(len(STEPS)))
    print(f"{W}x{H}: card {cw:.0f}x{ch:.0f}, tallest content {need:.0f}")
    if need > ch:
        print("  warning: estimated content taller than card; check the render")
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
             f'<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
             f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>',
             f'<rect width="{W}" height="{H}" fill="{BG}"/>',
             f'<text x="{mx}" y="{head["t_y"]}" font-size="{head["t"]}" font-weight="800" fill="{INK}" letter-spacing="-0.5">'
             f'Evidence-Linked Clinical Handoff: how it works</text>']
    for k, ln in enumerate(head["sub"]):
        parts.append(f'<text x="{mx}" y="{head["t_y"] + head["s"] * 1.5 * (k + 1) + 6}" font-size="{head["s"]}" fill="{MUTED}">{html.escape(ln)}</text>')
    pos = []
    for i in range(len(STEPS)):
        r, c = divmod(i, cols)
        x, y = mx + c * (cw + gx), top + r * (ch + gy)
        pos.append((x, y))
        parts.append(card(i, x, y, cw, ch, s))
    for i in range(len(STEPS) - 1):
        (x1, y1), (x2, y2) = pos[i], pos[i + 1]
        if y1 == y2:  # same row
            parts.append(arrow(x1 + cw + 6, y1 + ch / 2, x2 - 8, y2 + ch / 2))
        else:  # wrap to the next row: down from the card's bottom, across, into the next card's top
            midy = y1 + ch + gy / 2
            parts.append(f'<path d="M{x1 + cw / 2},{y1 + ch + 4} L{x1 + cw / 2},{midy} L{x2 + cw / 2},{midy} '
                         f'L{x2 + cw / 2},{y2 - 8}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round" '
                         f'marker-end="url(#ah)"/>')
    parts.append(f'<text x="{mx}" y="{H - s["foot"] / 2 + 6}" font-size="{s["ex"]}" fill="{MUTED}">'
                 f'Synthetic records only · decision support, not a prescription · github.com/DrAhmed7887/hack-clocked</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render(name: str, W: int, H: int) -> None:
    src, png = HERE / f"{name}.svg", HERE / f"{name}.png"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--window-size={W},{H}", f"--screenshot={png}", src.as_uri()],
                   check=True, capture_output=True)


def main() -> None:
    land = svg(1600, 900, 4, {"pad": 22, "tag": 15, "title": 25, "body": 19, "ex": 18, "gx": 34, "gy": 46, "mx": 32, "foot": 50},
               {"top": 136, "t_y": 66, "t": 38, "s": 21,
                "sub": ["Five Clocked endpoints, each with one job. Every sentence is verified against the source records, or labelled for what it is."]})
    (HERE / "workflow.svg").write_text(land)
    port = svg(1080, 1350, 2, {"pad": 20, "tag": 17, "title": 28, "body": 22, "ex": 20, "gx": 36, "gy": 24, "mx": 36, "foot": 46, "short": True},
               {"top": 176, "t_y": 62, "t": 40, "s": 25,
                "sub": ["Five Clocked endpoints, each with one job.", "Every sentence verified, or labelled for what it is."]})
    (HERE / "workflow_4x5.svg").write_text(port)
    render("workflow", 1600, 900)
    render("workflow_4x5", 1080, 1350)
    print("ok")


if __name__ == "__main__":
    main()
