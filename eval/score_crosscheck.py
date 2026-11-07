"""Score the independent cross-checks (Protect privacy gate, Compare agreement) on a set.
Usage: python3 eval/score_crosscheck.py [clean|hard] -> eval/CROSSCHECK_<set>.md"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from crosscheck import compare_check, privacy_gate  # noqa: E402
from handoff import build  # noqa: E402


def main() -> None:
    variant = sys.argv[1] if len(sys.argv) > 1 else "hard"
    folder = "packets" if variant == "clean" else "packets_hard"
    passed = items = flagged = extra = credits = 0
    rows = []
    files = sorted((ROOT / "data" / folder).glob("packet_*.json"))
    for f in files:
        p = json.loads(f.read_text())
        g = privacy_gate(p)
        c = compare_check(p, build(p))
        passed += g["passed"]
        items += len(c["rule_items"])
        flagged += len(c["also_flagged_by_compare"])
        extra += len(c["compare_only"])
        credits += g["credits"] + c["credits"]
        rows.append({"packet": p["packet_id"], "not_flagged": sorted(set(c["rule_items"]) - set(c["also_flagged_by_compare"])),
                     "compare_only": c["compare_only"]})
    lines = [f"# Cross-check results, {variant} set ({len(files)} packets)", "",
             "Produced by `python3 eval/score_crosscheck.py`. Synthetic data only.", "",
             f"- Privacy gate (Clocked Protect) passed: **{passed}/{len(files)}** packets",
             f"- Rule-found dose/stop/allergy conflicts also flagged by Clocked Compare: **{flagged}/{items}**",
             f"- Compare conflicts that no rule explained (shown to the clinician for review): **{extra}**",
             f"- Clocked credits (Protect + Compare, as charged when first run): {credits}", "",
             "## Not flagged by Compare", ""] + [f"- {r['packet']}: {r['not_flagged']}" for r in rows if r["not_flagged"]]
    lines += ["", "## Compare only", ""] + [f"- {r['packet']}: {o['between']} | {(o['a'] or '')[:80]!r} vs {(o['b'] or '')[:80]!r}"
                                            for r in rows for o in r["compare_only"]]
    (ROOT / "eval" / f"CROSSCHECK_{variant}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:8]))


if __name__ == "__main__":
    main()
