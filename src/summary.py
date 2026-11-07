"""Written handoff (rules R7, R7a, R7b).

1. Clocked Fill drafts one sentence per discrepancy, attributing exact quotes to named records.
2. Clocked Verify checks every drafted sentence against the ORIGINAL records; unsupported ones are removed and listed (R7).
3. R7a: a text checker cannot prove an absence, so a sentence about a medicine the comparison labelled
   "missing from the newest record", or about allergy information absent from every record, is kept and marked
   "established by record comparison".
4. R7b safety net: any discrepancy the kept text still does not name is added from the rules as a quoted sentence,
   marked "added by rules", and also sent to Verify so its verdict is shown.
An independent string check confirms no medicine is named that is not in the extracted facts.
"""
import re

from clocked import call
import normalize as nz

KIND = {"discharge": "discharge summary", "clinic": "clinic note", "pharmacy": "pharmacy record", "gp_letter": "GP letter"}
VERIFY_INSTRUCTIONS = ("The records are clinical documents about one patient written at different dates; they may "
                       "disagree. A sentence that attributes quoted words to a named record is supported when that record "
                       "contains those words. Spanish and English terms, and prescriber abbreviations such as BD, OD and "
                       "nocte, may express the same fact. Missing evidence is not proof that a statement is false.")


def _quote(doc: dict, span) -> str:
    if not span or span[0] is None:
        return ""
    return "".join(list(doc["text"])[span[0]:span[1]]).strip().lstrip("-–• ").strip()


def _items(handoff: dict, docs: list) -> list:
    """One item per discrepancy: (key term, template sentence built only from verbatim quotes)."""
    name = {d["doc_id"]: f"the {KIND.get(d['kind'], d['kind'])} of {d['date']}" for d in docs}
    by_id = {d["doc_id"]: d for d in docs}
    newest = docs[-1]["doc_id"]
    items = []
    if handoff["allergy_state"] == "conflicting":
        said = "; ".join(f"{name[k]} says '{'; '.join(v)}'" for k, v in handoff["allergy_sources"].items())
        items.append(("allergy", f"Allergy conflict: {said}."))
    for drug, m in sorted(handoff["medications"].items()):
        if m["label"] == "consistent":
            continue
        q = {k: _quote(by_id[k], v[0]) for k, v in m["sources"].items()}
        listed = "; ".join(f"{name[k]} says '{q[k]}'" for k in q)
        sentence = {
            "possible_omission": f"{drug.capitalize()} is listed in earlier records ({listed}) but not in {name[newest]}.",
            "dose_differs": f"{drug.capitalize()} differs between records: {listed}.",
            "new_start": f"{drug.capitalize()} appears only in {name[newest]}: '{q.get(newest, '')}'.",
            "stopped": f"{drug.capitalize()}: {listed}.",
        }[m["label"]]
        items.append((drug, sentence))
    return items


def _names(term: str, text: str) -> bool:
    if term == "allergy":
        return bool(re.search(r"allerg|alerg", text))
    words = [term] + [k for k, v in nz.DRUG_SYNONYMS.items() if v == term]
    return any(re.search(rf"\b{re.escape(w.split()[0])}\b", text) for w in words)


def write_and_verify(handoff: dict, packet: dict) -> dict:
    docs = sorted(packet["documents"], key=lambda d: d["date"])
    items = _items(handoff, docs)
    credits = 0
    kept, removed, added = [], [], []
    if items:
        sheet = "\n".join(f"- {s}" for _, s in items)
        draft = call("fill", {"text": sheet, "fields": {"handoff": {
            "type": "generate", "description": "The written handoff", "max_tokens": 400}},
            "instructions": ("Rewrite these items as a clear handoff for the receiving clinician, one sentence per item, "
                             "in the same order. Keep every quoted record text exactly as quoted and say which record it "
                             "comes from. Do not recommend any treatment, dose or action. Do not add any fact.")})
        text = (draft["fields"]["handoff"].get("value") or "").strip()
        credits += int(draft.get("_credits") or 0)
        check = call("grounding", {"documents": [{"id": d["doc_id"], "text": d["text"]} for d in docs], "answer": text,
                                   "instructions": VERIFY_INSTRUCTIONS, "evidence": "all", "threshold": 0.65})
        credits += int(check.get("_credits") or 0)
        absent = [d for d, m in handoff["medications"].items() if m["label"] == "possible_omission"]
        for c in check.get("claims", []):
            if c.get("verdict") == "not_a_claim" or c.get("kind") != "claim":
                continue
            row = {"sentence": c["claim"], "verdict": c.get("verdict"), "supported": c.get("supported"),
                   "evidence": (c.get("evidence") or {}).get("quote")}
            hit = [d for d in absent if _names(d, row["sentence"].lower())]
            if c.get("verdict") == "supported":
                kept.append(row)
            elif hit and c.get("verdict") == "not_stated":  # R7a
                row["established_by"] = f"record comparison (rule R4): {', '.join(hit)} absent from the newest record"
                kept.append(row)
            else:
                removed.append(row)
        covered = " ".join(r["sentence"].lower() for r in kept)
        missing = [(t, s) for t, s in items if not _names(t, covered)]
        if missing:  # R7b safety net
            net = call("grounding", {"documents": [{"id": d["doc_id"], "text": d["text"]} for d in docs],
                                     "answer": " ".join(s for _, s in missing), "claims": [s for _, s in missing][:30],
                                     "instructions": VERIFY_INSTRUCTIONS, "evidence": "all", "threshold": 0.65})
            credits += int(net.get("_credits") or 0)
            verdicts = {c["claim"]: c.get("verdict") for c in net.get("claims", [])}
            for t, s in missing:
                added.append({"sentence": s, "verdict": verdicts.get(s), "established_by": "added by rules (R7b)"})
    if handoff["allergy_state"] == "no_info":  # R3 + R7a: stated by comparison, not by text
        added.append({"sentence": "No record mentions allergies: allergy status is unknown, not 'no allergies'.",
                      "verdict": None, "established_by": "record comparison (rule R3)"})
    final = kept + added
    known = set(handoff["medications"])
    named = {d for d in set(nz.DRUG_SYNONYMS.values()) if _names(d, " ".join(r["sentence"].lower() for r in final))}
    return {"items": [s for _, s in items], "kept": kept, "added": added, "removed": removed, "final": final,
            "unknown_medicines_in_final_text": sorted(named - known), "credits": credits}
