"""Score the written handoff (Fill + Verify, rules R7/R7a) on every packet of a set.

Coverage = each planted discrepancy (non-consistent medicine, allergy conflict) is named in the KEPT sentences.
Usage: python3 eval/score_summary.py [clean|hard]  -> eval/SUMMARY_<set>.md
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from handoff import build  # noqa: E402
from summary import write_and_verify  # noqa: E402
import normalize as nz  # noqa: E402

ES = {v: k for k, v in nz.DRUG_SYNONYMS.items()}


def mentioned(term: str, text: str) -> bool:
    words = [term] + [k for k, v in nz.DRUG_SYNONYMS.items() if v == term]
    return any(re.search(rf"\b{re.escape(w.split()[0])}\b", text) for w in words)


def main() -> None:
    variant = sys.argv[1] if len(sys.argv) > 1 else "hard"
    folder = "packets" if variant == "clean" else "packets_hard"
    rows, tot = [], {"need": 0, "covered": 0, "kept_text": 0, "kept_cmp": 0, "removed": 0, "unknown": 0, "credits": 0}
    for f in sorted((ROOT / "data" / folder).glob("packet_*.json")):
        p = json.loads(f.read_text())
        s = write_and_verify(build(p), p)
        text = " ".join(r["sentence"].lower() for r in s["final"])
        need = [m["drug"] for m in p["truth"]["medications"] if m["label"] != "consistent"]
        if p["truth"]["allergy"]["state"] == "conflicting":
            need.append(p["truth"]["allergy"]["allergen"])
        missed = [n for n in need if not mentioned(n, text)
                  and not (n == p["truth"]["allergy"]["allergen"] and re.search(r"allerg|alerg", text))]
        tot["need"] += len(need)
        tot["covered"] += len(need) - len(missed)
        tot["kept_text"] += sum("established_by" not in r for r in s["kept"])
        tot["kept_cmp"] += sum("established_by" in r for r in s["kept"])
        tot["added"] = tot.get("added", 0) + sum("R7b" in r["established_by"] for r in s["added"])
        tot["added_ok"] = tot.get("added_ok", 0) + sum("R7b" in r["established_by"] and r["verdict"] == "supported" for r in s["added"])
        tot["removed"] += len(s["removed"])
        tot["unknown"] += len(s["unknown_medicines_in_final_text"])
        tot["credits"] += s["credits"]
        rows.append({"packet": p["packet_id"], "missed": missed, "removed": [r["sentence"] for r in s["removed"]],
                     "final": [[r["sentence"], r.get("established_by", "text evidence"), r.get("verdict")] for r in s["final"]]})
    (ROOT / "eval" / f"summary_{variant}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    lines = [f"# Written handoff results, {variant} set ({len(rows)} packets)", "",
             "Produced by `python3 eval/score_summary.py`. Synthetic data only.", "",
             f"- Discrepancies named in the final text: **{tot['covered']}/{tot['need']}**",
             f"- Generated sentences kept on text evidence (Clocked Verify): **{tot['kept_text']}**",
             f"- Sentences kept on record comparison (rule R7a): **{tot['kept_cmp']}**",
             f"- Sentences added by the rules safety net (R7b): **{tot.get('added', 0)}** (Verify supported {tot.get('added_ok', 0)} of them)",
             f"- Generated sentences removed as unsupported: **{tot['removed']}**",
             f"- Medicines named in the final text that are not in the records: **{tot['unknown']}**",
             f"- Clocked credits (Fill + Verify, as charged when first run): {tot['credits']}", "",
             "## Not covered", ""] + [f"- {r['packet']}: {r['missed']}" for r in rows if r["missed"]]
    lines += ["", "## Removed sentences", ""] + [f"- {r['packet']}: {x}" for r in rows for x in r["removed"]]
    (ROOT / "eval" / f"SUMMARY_{variant}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))


if __name__ == "__main__":
    main()
