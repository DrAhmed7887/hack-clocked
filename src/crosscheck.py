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
        if not isinstance(r.get("entities"), list):  # fail closed on an unexpected response (review PR#2 #1)
            hits.append({"doc": d["doc_id"], "type": "error", "allowed": False, "value": "unexpected Protect response"})
            continue
        for e in r["entities"]:
            allowed = (e.get("type") in ("person", "national_id")  # the label only ever appears as these (#2)
                       and bool(ALLOWED.match((e.get("value") or "").strip())))
            hits.append({"doc": d["doc_id"], "type": e.get("type"), "allowed": allowed,
                         "value": e.get("value") if allowed else "[redacted]"})  # never echo a real identifier
    return {"passed": not any(not h["allowed"] for h in hits), "hits": hits, "credits": credits}


def _short(side: dict) -> str:
    q = (side or {}).get("quote") or ""
    return q.lower() if len(q) <= 200 else ""  # a whole-document "quote" would match every medicine


def _mentions(words, text) -> bool:
    return any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", text) for w in words)


def match_conflicts(compare: dict, handoff: dict) -> dict:
    """Which rule discrepancies Compare also flagged, and which Compare conflicts no rule explains.

    A finding counts as explained only when its shape matches the rule label (review PR#2 #4): a finding that quotes
    the medicine on both sides is a value conflict (explained by dose_differs or stopped); one that quotes it on one
    side only is a presence conflict (explained by any non-consistent label). Allergy findings are explained only when
    the rules found an allergy conflict. Everything else is shown to the clinician as "Compare only".
    """
    pairs = compare.get("pairs")
    if not isinstance(pairs, list) or not isinstance(compare.get("conflicts", []), list):
        raise RuntimeError("unexpected Compare response shape")  # fail loudly (#5)
    findings = [(pairs[i]["a"], pairs[i]["b"], f) for i in compare.get("conflicts", []) for f in pairs[i].get("conflicts", [])]
    syn = lambda d: [d] + [k for k, v in nz.DRUG_SYNONYMS.items() if v == d]
    labels = {d: m["label"] for d, m in handoff["medications"].items()}
    targets = sorted([d for d, l in labels.items() if l in ("dose_differs", "stopped")]
                     + (["allergy"] if handoff["allergy_state"] == "conflicting" else []))
    explained, unexplained = set(), []
    for a, b, f in findings:
        qa, qb = _short(f.get("a")), _short(f.get("b"))
        ok = False
        for d, lab in labels.items():
            on_a, on_b = _mentions(syn(d), qa), _mentions(syn(d), qb)
            if on_a and on_b and lab in ("dose_differs", "stopped"):
                ok = True
                explained.add(d)
            elif (on_a or on_b) and not (on_a and on_b) and lab != "consistent":
                ok = True
                if d in targets:
                    explained.add(d)
        if re.search(r"allerg|alerg", f"{qa} {qb}") and handoff["allergy_state"] == "conflicting":
            ok = True
            explained.add("allergy")
        if not ok:
            unexplained.append({"between": [a, b], "a": (f.get("a") or {}).get("quote"), "b": (f.get("b") or {}).get("quote")})
    return {"rule_items": targets, "also_flagged_by_compare": sorted(explained & set(targets)), "compare_only": unexplained}


def compare_check(packet: dict, handoff: dict) -> dict:
    r = call("compare", {"documents": [{"id": d["doc_id"], "text": d["text"]} for d in packet["documents"]],
                         "evidence": "all", "instructions": COMPARE_INSTRUCTIONS})
    out = match_conflicts(r, handoff)
    out["credits"] = int(r.get("_credits") or 0)
    return out
