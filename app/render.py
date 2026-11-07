"""HTML rendering for the static site: one page per synthetic patient, plus the index and the method page."""
import html

KIND = {"discharge": "Discharge summary", "clinic": "Clinic note", "pharmacy": "Pharmacy record", "gp_letter": "GP letter"}
LABEL = {"consistent": ("Same in all records", "ok"), "dose_differs": ("Dose or timing differs", "warn"),
         "possible_omission": ("Missing from newest record", "warn"), "new_start": ("New in newest record", "info"),
         "stopped": ("Recorded as stopped", "info")}
ORDER = {"possible_omission": 0, "dose_differs": 1, "stopped": 2, "new_start": 3, "consistent": 4}

CSS = """:root{--bg:#f6f5f1;--card:#fff;--ink:#1d1d1b;--muted:#5d5d58;--line:#e2e0d8;--ok:#1f7a4d;--okbg:#e6f3ec;--warn:#9a5b00;--warnbg:#fdf0dc;--info:#2b5c9e;--infobg:#e7eef9;--red:#a4161a;--redbg:#fde8e8}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--card:#1f1f1c;--ink:#ecebe6;--muted:#a8a69e;--line:#34332e;--ok:#7fd1a5;--okbg:#173225;--warn:#f0b65a;--warnbg:#3a2a10;--info:#9cbcf0;--infobg:#1b2a42;--red:#ff9d9d;--redbg:#3d1416}}
*{box-sizing:border-box;min-width:0}html,body{overflow-x:hidden}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:760px;margin:0 auto;padding:16px}a{color:var(--info)}h1{font-size:1.4rem;margin:.3rem 0}h2{font-size:1.05rem;margin:1.5rem 0 .5rem}
.step{font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:.5rem 0}
.banner{background:var(--redbg);border:2px solid var(--red);color:var(--red);border-radius:12px;padding:12px 14px;margin:1rem 0}.banner ul{color:var(--ink);margin:.5rem 0 0;padding-left:1rem}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:.4rem 0;padding:.55rem .8rem}summary{cursor:pointer;display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
details ul{margin:.5rem 0 .2rem;padding-left:1rem}li{margin:.3rem 0}.src{display:block;font-size:.8rem;color:var(--muted)}
q{display:block;font-family:ui-monospace,Menlo,monospace;font-size:.86rem;quotes:"\\201C" "\\201D";overflow-wrap:anywhere}
.chip{font-size:.74rem;font-weight:600;border-radius:999px;padding:.1rem .55rem;white-space:nowrap}.ok{color:var(--ok);background:var(--okbg)}.warn{color:var(--warn);background:var(--warnbg)}.info{color:var(--info);background:var(--infobg)}.bad{color:var(--red);background:var(--redbg)}
.n{color:var(--muted);font-size:.8rem;margin-left:auto}.foot{font-size:.85rem;color:var(--muted);margin-top:1.6rem}.sent{margin:.55rem 0}.sent .chip{margin-right:.35rem}
nav{display:flex;gap:1rem;font-size:.9rem;margin-bottom:.6rem}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid var(--line);padding:.45rem .3rem;text-align:left;font-size:.92rem}"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def page(title: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{CSS}</style></head>'
            f'<body><main><nav><a href="../index.html">All patients</a><a href="../method.html">How it works</a></nav>'
            f'{body}</main></body></html>')


def quote(doc, span) -> str:
    if not span or span[0] is None:
        return "(no span)"
    return "".join(list(doc["text"])[span[0]:span[1]]).strip().lstrip("-–• ").strip()


def patient_page(packet: dict, h: dict, s: dict, x: dict = None) -> str:
    docs = {d["doc_id"]: d for d in packet["documents"]}
    ex = {e["doc_id"]: e for e in h["extracted"]}
    by_date = sorted(docs.values(), key=lambda d: d["date"])

    def src(doc_id):
        d = docs[doc_id]
        return f"{KIND.get(d['kind'], d['kind'])}, {d['date']}" + (" · Spanish" if d["kind"] == "gp_letter" else "")

    st = h["allergy_state"]
    alg = "".join(f"<li><span class='src'>{esc(src(k))}</span><q>{esc('; '.join(v))}</q></li>"
                  for k, v in h["allergy_sources"].items())
    banner = ("<div class='banner'><strong>Allergy conflict.</strong> One record lists an allergy, another says no known "
              f"drug allergies. Check with the patient before prescribing.<ul>{alg}</ul></div>") if st == "conflicting" else ""
    allergy_card = {"conflicting": "Conflicting: see the alert above.",
                    "known": f"Allergy recorded in every record that mentions allergies.<ul>{alg}</ul>",
                    "nkda": f"No known drug allergies, as stated in:<ul>{alg}</ul>",
                    "no_info": "<strong>No allergy information found in any record.</strong> Allergy status is unknown, "
                               "which is not the same as 'no allergies'."}[st]

    meds = ""
    for drug, m in sorted(h["medications"].items(), key=lambda kv: (ORDER[kv[1]["label"]], kv[0])):
        text, tone = LABEL[m["label"]]
        rows = ""
        for d in by_date:
            per = [x for x in ex[d["doc_id"]]["medications"] if x["drug"] == drug]  # every line, not just the first
            cell = "".join(f"<q>{esc(quote(d, x['span']))}</q>" for x in per) if per else "<em>not listed</em>"
            rows += f"<li><span class='src'>{esc(src(d['doc_id']))}</span>{cell}</li>"
        meds += (f"<details{' open' if tone == 'warn' else ''}><summary><span class='chip {tone}'>{text}</span>"
                 f"{esc(drug.capitalize())}</summary><ul>{rows}</ul></details>")

    probs = ""
    for name, refs in sorted(h["problems"].items()):
        cites = "".join(f"<li><span class='src'>{esc(src(r['doc']))}</span><q>{esc(quote(docs[r['doc']], r['span']))}</q></li>"
                        for r in refs)
        probs += (f"<details><summary><span class='chip ok'>Supported</span>{esc(name.capitalize())}"
                  f"<span class='n'>{len(refs)} record{'s' if len(refs) > 1 else ''}</span></summary><ul>{cites}</ul></details>")

    def badge(r):
        if "established_by" not in r:
            return "<span class='chip ok'>Verified in the records</span>"
        if "R7b" in r["established_by"]:
            v = r.get("verdict") or "not checked"
            if v == "supported":
                return "<span class='chip info'>Added by rules</span><span class='chip ok'>Each quote verified</span>"
            return (f"<span class='chip info'>Added by rules</span><span class='chip {'ok' if v == 'supported' else 'warn'}'>"
                    f"Verify: {esc(v.replace('_', ' '))}</span>")
        return "<span class='chip info'>Established by comparing records</span>"

    summary = "".join(f"<div class='sent'>{badge(r)}<br>{esc(r['sentence'])}</div>" for r in s["final"]) \
        or "<div class='sent'>No discrepancies between the records.</div>"
    removed = ""
    if s["removed"]:
        removed = ("<details><summary><span class='chip bad'>Removed</span>Sentences the checker could not support "
                   f"({len(s['removed'])})</summary><ul>"
                   + "".join(f"<li>{esc(r['sentence'])} <span class='src'>Verify: {esc(r['verdict'])}</span></li>"
                             for r in s["removed"]) + "</ul></details>")
    warn = "".join(f"<li>{esc(w)}</li>" for w in h.get("warnings", []))
    warn_box = f"<div class='banner'><strong>Extraction warnings.</strong><ul>{warn}</ul></div>" if warn else ""
    cross = ""
    if x:
        g, c = x["privacy"], x["compare"]
        gate = ("<span class='chip ok'>Privacy gate passed</span> Clocked Protect found no names, contact details, birth "
                "dates or ID numbers (only the synthetic case label).") if g["passed"] else (
                "<span class='chip bad'>Privacy gate failed</span> Identifiers found; records must be de-identified first.")
        flagged = ", ".join(esc(i) for i in c["also_flagged_by_compare"]) or "none"
        missing = [i for i in c["rule_items"] if i not in c["also_flagged_by_compare"]]
        extra = "".join(f"<li><span class='src'>{esc(' vs '.join(o['between']))}</span><q>{esc((o['a'] or '')[:160])}</q>"
                        f"<q>{esc((o['b'] or '')[:160])}</q></li>" for o in c["compare_only"])
        cross = (f"<h2>Independent cross-checks</h2><div class='card'><p>{gate}</p>"
                 f"<p><strong>Clocked Compare</strong>, run separately on the raw records, also flagged: {flagged}"
                 f"{'; not flagged by Compare: ' + ', '.join(esc(i) for i in missing) if missing else ''}.</p>"
                 + (f"<details><summary><span class='chip warn'>Compare only</span>Conflicts no rule explained "
                    f"({len(c['compare_only'])}): review</summary><ul>{extra}</ul></details>" if extra else "")
                 + "</div>")
    record_list = "".join(f"<li>{esc(src(d['doc_id']))}</li>" for d in by_date)
    raw = "".join(f"<details><summary>{esc(src(d['doc_id']))}</summary><pre style='white-space:pre-wrap;font-size:.85rem'>"
                  f"{esc(d['text'])}</pre></details>" for d in by_date)
    body = f"""<div class="step">Synthetic patient {esc(packet['packet_id'])}</div>
<h1>Evidence-linked handoff</h1>
<p>Every fact links to the exact words in a source record. Conflicts are shown side by side, never resolved for you.</p>
<div class="card"><strong>{len(docs)} records</strong><ul>{record_list}</ul></div>
{banner}{warn_box}
<h2>Written handoff</h2><div class="card">{summary}{removed}</div>
<h2>Allergies &amp; intolerances</h2><div class="card">{allergy_card}</div>
<h2>Medications</h2>{meds}
<h2>Problems</h2>{probs or '<div class="card">No problems listed in any record.</div>'}
{cross}
<h2>The source records</h2>{raw}
<p class="foot">Decision support for a clinician, not a diagnosis or a prescription. Synthetic records only, no real
patients. Facts copied by Clocked Extract; labels set by fixed, physician-signed rules; written handoff drafted by
Clocked Fill and checked sentence by sentence by Clocked Verify against the original records.</p>"""
    return page(f"Handoff {packet['packet_id']}", body)
