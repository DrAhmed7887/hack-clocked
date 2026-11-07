"""Independent cross-checks with two more Clocked endpoints.

Protect (/clocked/pii): a privacy gate. Every record is scanned for names, contact details, birth dates and ID numbers
before anything else runs; only the synthetic case label is allow-listed. Any other hit stops processing.
Compare (/clocked/compare): an independent conflict detector across the records. Its conflicts are matched against the
discrepancies found by the fixed rules, and any conflict the rules did not explain is listed for the clinician.
"""
import re

from clocked import call
import normalize as nz

PII_ENTITIES = {"person": "Full names of people", "phone": "Phone numbers", "email": "Email addresses",
                "address": "Street addresses", "date_of_birth": "Birth dates",
                "national_id": "Passport, national ID, social security or medical record numbers"}
ALLOWED = re.compile(r"^((synthetic case|caso sintético) )?P\d{3}$", re.I)
COMPARE_INSTRUCTIONS = (
    "The records describe the same patient at different dates. A conflict is a different dose or frequency of the "
    "same medicine, a medicine recorded as stopped in one record and active in another, or an allergy in one record "
    "and no known allergies in another. Spanish and English, and prescriber abbreviations such as BD, OD and nocte, "
    "can state the same thing. A different date alone is not a conflict.")


def privacy_gate(packet: dict) -> dict:
    hits, credits = [], 0
    for d in packet["documents"]:
        r = call("pii", {"text": d["text"], "entities": PII_ENTITIES, "threshold": 0.5})
        credits += int(r.get("_credits") or 0)
        for e in r.get("entities", []):
            allowed = bool(ALLOWED.match((e.get("value") or "").strip()))
            hits.append({"doc": d["doc_id"], "type": e.get("type"), "allowed": allowed,
                         "value": e.get("value") if allowed else "[redacted]"})  # never echo a real identifier
    return {"passed": not any(not h["allowed"] for h in hits), "hits": hits, "credits": credits}


def _short(side: dict) -> str:
    q = (side or {}).get("quote") or ""
    return q.lower() if len(q) <= 200 else ""  # a whole-document "quote" would match every medicine


def match_conflicts(compare: dict, handoff: dict) -> dict:
    """Which rule discrepancies Compare also flagged, and which Compare conflicts no rule explains."""
    findings = [(p["a"], p["b"], f) for i in compare.get("conflicts", []) for p in [compare["pairs"][i]]
                for f in p.get("conflicts", [])]
    targets = {d: [d] + [k for k, v in nz.DRUG_SYNONYMS.items() if v == d]
               for d, m in handoff["medications"].items() if m["label"] in ("dose_differs", "stopped")}
    if handoff["allergy_state"] == "conflicting":
        targets["allergy"] = ["allerg", "alerg"]
    # Any finding about a medicine the rules already flagged (omissions and new starts too) is explained by them.
    all_flagged = dict(targets, **{d: [d] + [k for k, v in nz.DRUG_SYNONYMS.items() if v == d]
                                   for d, m in handoff["medications"].items() if m["label"] != "consistent"})
    explained, unexplained = set(), []
    for a, b, f in findings:
        text = f"{_short(f.get('a'))} {_short(f.get('b'))}"
        hit = [t for t, words in all_flagged.items() if any(re.search(rf"(?<![a-z]){re.escape(w)}", text) for w in words)]
        explained.update(h for h in hit if h in targets)
        if not hit:
            unexplained.append({"between": [a, b], "a": (f.get("a") or {}).get("quote"), "b": (f.get("b") or {}).get("quote")})
    return {"rule_items": sorted(targets), "also_flagged_by_compare": sorted(explained),
            "compare_only": unexplained}


def compare_check(packet: dict, handoff: dict) -> dict:
    r = call("compare", {"documents": [{"id": d["doc_id"], "text": d["text"]} for d in packet["documents"]],
                         "evidence": "all", "instructions": COMPARE_INSTRUCTIONS})
    out = match_conflicts(r, handoff)
    out["credits"] = int(r.get("_credits") or 0)
    return out
