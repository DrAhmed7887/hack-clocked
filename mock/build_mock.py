"""G2 mock: render the clinician's handoff screen from real (cached) Clocked output for one synthetic packet.

Usage: python3 mock/build_mock.py [packet file]  -> mock/index.html (static, no JS needed)
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from handoff import build  # noqa: E402

LABEL_TEXT = {"consistent": ("Same in all sources", "ok"), "dose_differs": ("Dose or timing differs", "warn"),
              "possible_omission": ("Missing from newest record", "warn"), "new_start": ("New in newest record", "info"),
              "stopped": ("Recorded as stopped", "info")}
KIND = {"discharge": "Discharge summary", "clinic": "Clinic note", "pharmacy": "Pharmacy record", "gp_letter": "GP letter"}


def esc(s):
    return html.escape(str(s or ""))


def quote(doc_text, span):
    a, b = span if span and span[0] is not None else (0, 0)
    chars = list(doc_text)
    return "".join(chars[a:b]).strip().lstrip("-–• ").strip() or "(no span)"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/packets_hard/packet_01.json"
    packet = json.loads(path.read_text())
    docs = {d["doc_id"]: d for d in packet["documents"]}
    out = build(packet)
    ex = {e["doc_id"]: e for e in out["extracted"]}

    def src_label(doc_id):
        d = docs[doc_id]
        lang = " · Spanish" if d["kind"] == "gp_letter" else ""
        return f"{KIND.get(d['kind'], d['kind'])}, {d['date']}{lang}"

    # Allergy block (R3, R5, R6)
    state = out["allergy_state"]
    allergy_rows = "".join(
        f"<li><span class='src'>{esc(src_label(k))}</span><q>{esc('; '.join(v))}</q></li>"
        for k, v in out["allergy_sources"].items())
    banner = ""
    if state == "conflicting":
        banner = ("<div class='banner'><strong>Allergy conflict.</strong> One record lists an allergy, another says "
                  f"no known drug allergies. Check with the patient before prescribing.<ul>{allergy_rows}</ul></div>")
    allergy_state_text = {"conflicting": "Conflicting: see the alert above", "known": "Allergy recorded",
                          "nkda": "No known drug allergies (stated)", "no_info": "No allergy information found in any record"}[state]

    # Problems (R2)
    prob_items = ""
    for name, refs in sorted(out["problems"].items()):
        cites = "".join(f"<li><span class='src'>{esc(src_label(r['doc']))}</span><q>{esc(quote(docs[r['doc']]['text'], r['span']))}</q></li>"
                        for r in refs)
        prob_items += (f"<details><summary><span class='chip ok'>Supported</span> {esc(name.capitalize())} "
                       f"<span class='n'>{len(refs)} source{'s' if len(refs) > 1 else ''}</span></summary><ul>{cites}</ul></details>")

    # Medications (R4, R5)
    order = {"possible_omission": 0, "dose_differs": 1, "stopped": 2, "new_start": 3, "consistent": 4}
    med_items = ""
    for drug, m in sorted(out["medications"].items(), key=lambda kv: (order[kv[1]["label"]], kv[0])):
        text, tone = LABEL_TEXT[m["label"]]
        rows = ""
        for d in sorted(docs.values(), key=lambda d: d["date"]):
            per = next((x for x in ex[d["doc_id"]]["medications"] if x["drug"] == drug), None)
            cell = f"<q>{esc(quote(d['text'], per['span']))}</q>" if per else "<em>not listed</em>"
            rows += f"<li><span class='src'>{esc(src_label(d['doc_id']))}</span>{cell}</li>"
        med_items += (f"<details{' open' if tone == 'warn' else ''}><summary><span class='chip {tone}'>{text}</span> "
                      f"{esc(drug.capitalize())}</summary><ul>{rows}</ul></details>")

    doc_list = "".join(f"<li>{esc(src_label(d['doc_id']))}</li>" for d in sorted(docs.values(), key=lambda d: d["date"]))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Handoff mock</title><style>
:root{{--bg:#f6f5f1;--card:#fff;--ink:#1d1d1b;--muted:#5d5d58;--line:#e2e0d8;--ok:#1f7a4d;--okbg:#e6f3ec;--warn:#9a5b00;--warnbg:#fdf0dc;--info:#2b5c9e;--infobg:#e7eef9;--red:#a4161a;--redbg:#fde8e8}}
*{{box-sizing:border-box;min-width:0}}html,body{{overflow-x:hidden}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
main{{max-width:720px;margin:0 auto;padding:16px}}h1{{font-size:1.35rem;margin:.2rem 0}}h2{{font-size:1.05rem;margin:1.4rem 0 .5rem}}
.step{{font-size:.8rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}}.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:.5rem 0}}
.banner{{background:var(--redbg);border:2px solid var(--red);color:var(--red);border-radius:12px;padding:12px 14px;margin:1rem 0}}.banner ul{{color:var(--ink);margin:.5rem 0 0;padding-left:1rem}}
details{{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:.4rem 0;padding:.55rem .8rem}}summary{{cursor:pointer;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}}
details ul{{margin:.5rem 0 .2rem;padding-left:1rem}}li{{margin:.25rem 0}}.src{{display:block;font-size:.8rem;color:var(--muted)}}q{{display:block;font-family:ui-monospace,Menlo,monospace;font-size:.86rem;quotes:"“" "”";overflow-wrap:anywhere;white-space:normal}}
.chip{{font-size:.75rem;font-weight:600;border-radius:999px;padding:.1rem .55rem;white-space:nowrap}}.ok{{color:var(--ok);background:var(--okbg)}}.warn{{color:var(--warn);background:var(--warnbg)}}.info{{color:var(--info);background:var(--infobg)}}
.n{{color:var(--muted);font-size:.8rem;margin-left:auto}}.foot{{font-size:.85rem;color:var(--muted);margin-top:1.5rem}}.todo{{border-style:dashed;color:var(--muted)}}
</style></head><body><main>
<div class="step">Step 1 of 2 · Records added</div>
<div class="card"><strong>{len(docs)} documents</strong> for synthetic patient {esc(packet['packet_id'])}<ul>{doc_list}</ul></div>
<div class="step">Step 2 of 2 · Handoff</div>
<h1>Evidence-linked handoff</h1>
<p>Every fact links to the exact words in the source record. Conflicts are shown side by side, never resolved for you.</p>
{banner}
<h2>Allergies &amp; intolerances</h2><div class="card">{esc(allergy_state_text)}</div>
<h2>Medications</h2>{med_items}
<h2>Problems</h2>{prob_items}
<h2>Summary for the receiving clinician</h2>
<div class="card todo">Next step to build: a short written handoff generated with Clocked Fill, with every sentence checked against the records by Clocked Verify. Unsupported sentences are removed and listed here (rule R7).</div>
<p class="foot">Decision support for a clinician, not a diagnosis or a prescription (rule R8). Synthetic records only. Facts copied by Clocked Extract; labels set by fixed rules, not by a model.</p>
</main></body></html>"""
    (ROOT / "mock" / "index.html").write_text(page)
    print("wrote mock/index.html; credits (cached):", out["credits"])


if __name__ == "__main__":
    main()
