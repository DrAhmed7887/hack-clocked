"""Build the static demo site from real Clocked responses (cached in runs/raw/; rerun with your own key to refresh).

Usage: python3 app/build_site.py  -> site/index.html, site/method.html, site/p/P001.html ...
No API key or call ever reaches the browser: the site is plain HTML.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "app"))
from handoff import build  # noqa: E402
from summary import write_and_verify  # noqa: E402
from crosscheck import compare_check, privacy_gate  # noqa: E402
from render import esc, page, patient_page  # noqa: E402

SITE = ROOT / "site"


def md_numbers(path: Path) -> str:
    """Bullet lines of a results file, as HTML (numbers come only from the eval scripts)."""
    lines = [l[2:] for l in path.read_text().splitlines() if l.startswith("- ") and "**" in l]
    bold = re.compile(r"[*][*](.+?)[*][*]")
    items = [bold.sub(lambda m: "<strong>" + m.group(1) + "</strong>", esc(l)) for l in lines]
    return "<ul>" + "".join("<li>" + i + "</li>" for i in items) + "</ul>"


def main() -> None:
    (SITE / "p").mkdir(parents=True, exist_ok=True)
    rows = ""
    for f in sorted((ROOT / "data" / "packets_hard").glob("packet_*.json")):
        p = json.loads(f.read_text())
        gate = privacy_gate(p)
        if not gate["passed"]:  # nothing else runs on records that carry identifiers
            raise SystemExit(f"{p['packet_id']}: privacy gate failed: {gate['hits']}")
        h = build(p)
        s = write_and_verify(h, p)
        x = {"privacy": gate, "compare": compare_check(p, h)}
        pid = re.sub(r"[^A-Za-z0-9_-]", "", p["packet_id"])  # safe filename (review: packet_id unescaped)
        (SITE / "p" / f"{pid}.html").write_text(patient_page(p, h, s, x))
        flags = sum(m["label"] != "consistent" for m in h["medications"].values())
        alert = {"conflicting": "<span class='chip bad'>Allergy conflict</span>",
                 "no_info": "<span class='chip warn'>No allergy info</span>"}.get(h["allergy_state"], "")
        langs = " · includes Spanish" if any(d["kind"] == "gp_letter" for d in p["documents"]) else ""
        rows += (f"<tr><td><a href='p/{pid}.html'>{esc(pid)}</a></td><td>{len(p['documents'])} records{langs}</td>"
                 f"<td>{alert} <span class='chip {'warn' if flags else 'ok'}'>{flags} medication flag{'s' if flags != 1 else ''}</span></td></tr>")
    film = ('<div class="card"><video src="film.mp4" controls preload="metadata" style="width:100%;border-radius:8px"></video>'
            '<p class="foot">Demo film, 2:32: one allergy sentence through Protect, Extract, the rules, Fill and Verify.</p></div>'
            if (SITE / "film.mp4").exists() else "")
    index = f"""<div class="step">Clocked Build Challenge 2026</div><h1>Evidence-Linked Clinical Handoff</h1>
<p>When a patient arrives with records from several countries, the receiving clinician needs to know which facts are
supported, which conflict, and which are missing. This tool reads every record, labels each medication, allergy and
problem, quotes the exact source words, and writes a short handoff drafted by Clocked Fill and checked sentence by sentence by
Clocked Verify. Sentences the checker cannot confirm are removed; absences and gaps are filled from fixed rules and labelled.</p>
{film}<p>Pick a synthetic patient. Each has 2 to 4 records from Cairo, Alexandria and Valencia; Valencia GP letters are in Spanish.</p>
<div class="card"><table><tr><th>Patient</th><th>Records</th><th>Flags</th></tr>{rows}</table></div>
<p class="foot">Synthetic records only, no real patients. Decision support for clinicians, not a diagnosis or a prescription.</p>"""
    (SITE / "index.html").write_text(page("Evidence-Linked Clinical Handoff", index).replace('href="../', 'href="'))
    method = f"""<h1>How it works, and how well</h1>
<h2>Pipeline</h2><ol>
<li><strong>Clocked Extract</strong> copies problems, allergies and medication lines from each record, with exact character positions.</li>
<li><strong>Fixed rules</strong> (signed by a physician) normalise shorthand and Spanish, then label each medication: same, dose differs, missing from newest, new, stopped; and each allergy state: recorded, conflicting, none known, no information. No model decides a label.</li>
<li><strong>Clocked Fill</strong> drafts one sentence per discrepancy, quoting the records.</li>
<li><strong>Clocked Verify</strong> checks every sentence against the original records. Unsupported sentences are removed and shown. Absences are established by comparison, because a text checker cannot prove that something is missing. A rules safety net adds any discrepancy the draft left out.</li></ol>
<p>Two independent cross-checks run on every patient: <strong>Clocked Protect</strong> scans each record for names,
contact details, birth dates and ID numbers before anything else runs, and <strong>Clocked Compare</strong> looks for
conflicts across the raw records on its own, so its findings can be matched against the rules.</p>
<h2>Measured results on realistic wording (20 synthetic patients, shorthand + Spanish)</h2>{md_numbers(ROOT / 'eval' / 'RESULTS_hard.md')}
<h2>The same records without shorthand and Spanish normalisation (baseline)</h2>{md_numbers(ROOT / 'eval' / 'RESULTS_hard_raw.md')}
<h2>Written handoff</h2>{md_numbers(ROOT / 'eval' / 'SUMMARY_hard.md')}
<h2>Cross-checks</h2>{md_numbers(ROOT / 'eval' / 'CROSSCHECK_hard.md')}
<p class="foot">Numbers come from <code>eval/score.py</code> and <code>eval/score_summary.py</code> in the repository. Synthetic data: they describe this test set, not real-world accuracy.</p>"""
    (SITE / "method.html").write_text(page("How it works", method).replace('href="../', 'href="'))
    print("site built:", len(list((SITE / "p").glob("*.html"))), "patient pages")


if __name__ == "__main__":
    main()
