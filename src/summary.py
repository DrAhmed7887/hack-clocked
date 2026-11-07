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
    items, claims = [], {}
    if handoff["allergy_state"] == "conflicting":
        said = "; ".join(f"{name[k]} says '{'; '.join(v)}'" for k, v in handoff["allergy_sources"].items())
        items.append(("allergy", f"Allergy conflict: {said}."))
        claims["allergy"] = [f"{name[k][0].upper() + name[k][1:]} says '{'; '.join(v)}'." for k, v in handoff["allergy_sources"].items()]
    for drug, m in sorted(handoff["medications"].items()):
        if m["label"] == "consistent":
            continue
        q = {k: " / ".join(_quote(by_id[k], sp) for sp in v["spans"]) for k, v in m["sources"].items()}
        listed = "; ".join(f"{name[k]} says '{q[k]}'" for k in q)
        claims[drug] = [f"{name[k][0].upper() + name[k][1:]} says '{q[k]}'." for k in q]
        sentence = {
            "possible_omission": f"{drug.capitalize()} is listed in earlier records ({listed}) but not in {name[newest]}.",
            "dose_differs": f"{drug.capitalize()} differs between records: {listed}.",
            "new_start": f"{drug.capitalize()} appears only in {name[newest]}: '{q.get(newest, '')}'.",
            "stopped": f"{drug.capitalize()}: {listed}.",
        }[m["label"]]
        items.append((drug, sentence))
    return items, claims


def _names(term: str, text: str) -> bool:
    """Full-name match (review finding 6): 'insulin glargine' never counts as naming 'insulin lispro'."""
    if term == "allergy":
        return bool(re.search(r"allergy conflict|conflicto de alergia", text))
    words = [term] + [k for k, v in nz.DRUG_SYNONYMS.items() if v == term]
    return any(re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", text) for w in words)


def write_and_verify(handoff: dict, packet: dict) -> dict:
    docs = sorted(packet["documents"], key=lambda d: d["date"])
    items, item_claims = _items(handoff, docs)
    credits = 0
    kept, removed, added = [], [], []
    if items:
        sheet = "\n".join(f"- {s}" for _, s in items)
        draft = call("fill", {"text": sheet, "fields": {"handoff": {
            "type": "generate", "description": "The written handoff", "max_tokens": 400}},
            "instructions": ("Rewrite these items as a clear handoff for the receiving clinician, one sentence per item, "
                             "in the same order. Start each sentence with the medicine name (or 'Allergy conflict') and "
                             "what changed, in plain words: stopped, dose differs, missing from the newest record, or new. "
                             "Then give the evidence: keep every quoted record text exactly as quoted and say which record "
                             "it comes from. Do not recommend any treatment, dose or action. Do not add any fact.")})
        text = (draft["fields"]["handoff"].get("value") or "").strip()
        credits += int(draft.get("_credits") or 0)
        check = call("grounding", {"documents": [{"id": d["doc_id"], "text": d["text"]} for d in docs], "answer": text,
                                   "instructions": VERIFY_INSTRUCTIONS, "evidence": "all", "threshold": 0.65})
        credits += int(check.get("_credits") or 0)
        absent = [d for d, m in handoff["medications"].items() if m["label"] == "possible_omission"]
        template = dict(items)
        for c in check.get("claims", []):
            if c.get("verdict") == "not_a_claim" or c.get("kind") != "claim":
                continue
            row = {"sentence": c["claim"], "verdict": c.get("verdict"), "supported": c.get("supported"),
                   "evidence": (c.get("evidence") or {}).get("quote")}
            hit = [d for d in absent if _names(d, row["sentence"].lower())]
            if c.get("verdict") == "supported":
                kept.append(row)
            elif hit and c.get("verdict") == "not_stated":  # R7a: keep the rule-built sentence, never Fill's wording
                for d in hit:  # (review finding 7: Fill text could carry an invented detail)
                    if not any(r.get("drug") == d for r in kept):
                        kept.append({"sentence": template[d], "drug": d, "verdict": c.get("verdict"),
                                     "established_by": f"record comparison (rule R4): {d} absent from the newest record"})
            else:
                removed.append(row)
        covered = " ".join(r["sentence"].lower() for r in kept)
        missing = [(t, s) for t, s in items if not _names(t, covered)]
        if missing:  # R7b safety net: each record's quoted words verified as a separate claim
            parts = {s: item_claims.get(t, [s]) for t, s in missing}  # built from the quote lists, not parsed back
            claims = [c for ps in parts.values() for c in ps][:30]
            net = call("grounding", {"documents": [{"id": d["doc_id"], "text": d["text"]} for d in docs],
                                     "answer": " ".join(claims), "claims": claims,
                                     "instructions": VERIFY_INSTRUCTIONS, "evidence": "all", "threshold": 0.65})
            credits += int(net.get("_credits") or 0)
            verdicts = {c["claim"]: c.get("verdict") for c in net.get("claims", [])}
            for t, s in missing:
                vs = [verdicts.get(c) for c in parts[s]]
                verdict = "supported" if vs and all(v == "supported" for v in vs) else next(
                    (v for v in vs if v not in (None, "supported")), None)
                absence = t != "allergy" and handoff["medications"][t]["label"] in ("possible_omission", "new_start")
                added.append({"sentence": s, "verdict": verdict, "parts": dict(zip(parts[s], vs)),
                              "absence_by_rules": absence,  # the "missing from / only in" part is not a quote (#7)
                              "established_by": "added by rules (R7b)"})
    if handoff["allergy_state"] == "no_info":  # R3 + R7a: stated by comparison, not by text
        added.append({"sentence": "No record mentions allergies: allergy status is unknown, not 'no allergies'.",
                      "verdict": None, "established_by": "record comparison (rule R3)"})
    # R6: allergy statements always come first.
    final = sorted(kept + added, key=lambda r: 0 if re.search(r"allerg|alerg", r["sentence"].lower()) else 1)
    known = set(handoff["medications"])
    named = {d for d in set(nz.DRUG_SYNONYMS.values()) if _names(d, " ".join(r["sentence"].lower() for r in final))}
    return {"items": [s for _, s in items], "kept": kept, "added": added, "removed": removed, "final": final,
            "unknown_medicines_in_final_text": sorted(named - known), "credits": credits}
