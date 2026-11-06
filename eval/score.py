"""Gate G1: run every synthetic packet through the handoff and score it against the answer key.

Writes eval/results.json and eval/RESULTS.md. Every public number must come from this script.
Usage: python3 eval/score.py [N]   (N = first N packets; default all)
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from handoff import build  # noqa: E402


def score_packet(packet: dict) -> dict:
    out = build(packet)
    t = packet["truth"]
    rows = {"allergy": (t["allergy"]["state"], out["allergy_state"])}
    med_rows = []
    for m in t["medications"]:
        got = out["medications"].get(m["drug"], {}).get("label", "MISSING")
        med_rows.append((m["drug"], m["label"], got))
    truth_drugs = {m["drug"] for m in t["medications"]}
    invented_meds = [d for d in out["medications"] if d not in truth_drugs]
    truth_probs = {p["name"] for p in t["problems"] if p["status"] == "supported"}
    got_probs = set(out["problems"])
    return {"packet": packet["packet_id"], "allergy": rows["allergy"], "meds": med_rows,
            "invented_meds": invented_meds, "missed_problems": sorted(truth_probs - got_probs),
            "invented_problems": sorted(got_probs - truth_probs), "credits": out["credits"]}


def main() -> None:
    files = sorted((ROOT / "data" / "packets").glob("packet_*.json"))
    if len(sys.argv) > 1:
        files = files[: int(sys.argv[1])]
    results = [score_packet(json.loads(f.read_text())) for f in files]
    (ROOT / "eval" / "results.json").write_text(json.dumps(results, indent=1))

    allergy_ok = sum(r["allergy"][0] == r["allergy"][1] for r in results)
    conf = Counter((r["allergy"][0], r["allergy"][1]) for r in results)
    allergy_conflicts = [r for r in results if r["allergy"][0] == "conflicting"]
    caught = sum(r["allergy"][1] == "conflicting" for r in allergy_conflicts)
    med = [m for r in results for m in r["meds"]]
    med_ok = sum(m[1] == m[2] for m in med)
    per_label = Counter(m[1] for m in med)
    per_label_ok = Counter(m[1] for m in med if m[1] == m[2])
    nonconsistent = [m for m in med if m[1] != "consistent"]
    flagged = sum(m[2] not in ("consistent", "MISSING") for m in nonconsistent)
    lines = [
        f"# G1 results ({len(results)} synthetic packets, {sum(len(json.loads(f.read_text())['documents']) for f in files)} documents)",
        "", "Produced by `python3 eval/score.py`. Synthetic data only.", "",
        f"- Allergy state correct: **{allergy_ok}/{len(results)}**",
        f"- Allergy conflicts flagged: **{caught}/{len(allergy_conflicts)}**",
        f"- Medication labels correct: **{med_ok}/{len(med)}**",
        f"- Medication discrepancies flagged (any non-consistent label): **{flagged}/{len(nonconsistent)}**",
        f"- Invented medications: **{sum(len(r['invented_meds']) for r in results)}**; "
        f"invented problems: **{sum(len(r['invented_problems']) for r in results)}**; "
        f"missed problems: **{sum(len(r['missed_problems']) for r in results)}**",
        f"- Clocked credits used (this run, excluding cached calls): {sum(r['credits'] or 0 for r in results)}",
        "", "| Medication label | correct |", "|---|---|"]
    lines += [f"| {k} | {per_label_ok[k]}/{v} |" for k, v in sorted(per_label.items())]
    lines += ["", "Allergy (truth → got): " + ", ".join(f"{a}→{b}: {n}" for (a, b), n in sorted(conf.items()))]
    errs = [(r["packet"], m) for r in results for m in r["meds"] if m[1] != m[2]]
    lines += ["", "## Medication errors", ""] + [f"- {p}: {d} truth={a} got={b}" for p, (d, a, b) in errs[:40]]
    extra = [(r["packet"], r["invented_meds"], r["invented_problems"], r["missed_problems"]) for r in results
             if r["invented_meds"] or r["invented_problems"] or r["missed_problems"]]
    lines += ["", "## Invented / missed", ""] + [f"- {p}: invented meds {a}, invented problems {b}, missed problems {c}"
                                                    for p, a, b, c in extra]
    (ROOT / "eval" / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
