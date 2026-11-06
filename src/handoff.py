"""Evidence-linked handoff: Clocked Extract per document, then deterministic labelling under rules R2-R5.

No model decides a label. The model only copies spans (Extract); the rules below compare them.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from clocked import call
import normalize as nz

FIELDS = {
    "problems": {"description": "Every diagnosis or long-term condition under the Problems or Antecedentes heading, one item per line, including lines that start with 'Known', 'History of' or a dash. Copy each condition verbatim.",
                 "list": True, "max_items": 12},
    "allergies": {"description": "Each drug or substance allergy with its reaction, verbatim. Do not include statements that there are no allergies.",
                  "list": True, "max_items": 8},
    "no_known_allergies": "A sentence stating the patient has no known drug allergies, verbatim; empty if there is none",
    "medications": {"description": "Each medication line", "list": True, "max_items": 16,
                    "fields": {"line": "The whole medication line, verbatim, from the medicine name to the end of the line",
                               "drug": "Medicine name only",
                               "dose": "Strength or amount, e.g. '500 mg' or '16 units'; empty if not stated",
                               "frequency": "How often it is taken; empty if not stated",
                               "stopped": "The words saying the medicine was stopped, e.g. 'stopped on 2025-01-02'; empty if not stopped"},
                    "row_anchor": "drug"},
}
INSTRUCTIONS = ("This is one clinical document about one synthetic patient. Copy values verbatim. "
                "Leave a field empty when the document does not state it; never infer.")


def _val(field):
    return field.get("value") if isinstance(field, dict) else None


def extract_document(doc: dict) -> dict:
    r = call("extract", {"text": doc["text"], "fields": FIELDS, "instructions": INSTRUCTIONS})
    f = r["fields"]
    meds = []
    for item in f.get("medications", {}).get("items", []) or []:
        cols = item.get("fields", {})
        get = lambda k: (cols.get(k) or {}).get("value")
        if get("drug"):
            stopped = get("stopped") or (get("line") if nz.is_stop(get("line")) else None)
            meds.append({"drug": nz.drug(get("drug")), "as_written": get("drug"), "line": get("line"),
                         "dose": get("dose"), "frequency": get("frequency"),
                         "stopped": stopped, "span": [item.get("start"), item.get("end")]})
    problems = []
    for it in (f.get("problems", {}).get("items") or []):
        for part in (it.get("value") or "").split("\n"):  # a span can run across two lines; keep each line
            if part.strip(" .-") and part.strip(" .-").lower() not in ("none recorded", "sin antecedentes registrados"):
                problems.append({"name": nz.problem(part), "as_written": part, "span": [it.get("start"), it.get("end")]})
    allergies = [{"text": it["value"], "span": [it.get("start"), it.get("end")]}
                 for it in (f.get("allergies", {}).get("items") or []) if it.get("value")]
    nkda = _val(f.get("no_known_allergies"))
    return {"doc_id": doc["doc_id"], "date": doc["date"], "kind": doc["kind"], "problems": problems,
            "allergies": allergies, "nkda": nkda, "medications": meds, "credits": r.get("_credits")}


def _norm_dose(m: dict) -> str:
    """Dose + frequency as written. Uses the whole verbatim line (minus the drug name) when available, because
    separate dose/frequency spans can be cut at different points in different documents (G1, 7 Nov)."""
    return nz.regimen(m.get("line") or f"{m.get('dose') or ''} {m.get('frequency') or ''}", m["drug"])


def label(extracted: list) -> dict:
    """Apply R2-R5 to the per-document extractions (sorted by date; the newest is NOT assumed correct)."""
    docs = sorted(extracted, key=lambda d: d["date"])
    newest = docs[-1]
    # R3 / R5 / R6: allergies
    has_allergy = [d for d in docs if d["allergies"]]
    has_nkda = [d for d in docs if d["nkda"]]
    if has_allergy and has_nkda:
        allergy_state = "conflicting"
    elif has_allergy:
        allergy_state = "known"
    elif has_nkda:
        allergy_state = "nkda"
    else:
        allergy_state = "no_info"
    # R2: problems (supported if any source states it)
    problems = {}
    for d in docs:
        for p in d["problems"]:
            problems.setdefault(p["name"], []).append({"doc": d["doc_id"], "span": p["span"]})
    # R4: medications
    meds = {}
    for d in docs:
        for m in d["medications"]:
            meds.setdefault(m["drug"], {})[d["doc_id"]] = m
    med_labels = {}
    older_ids = [d["doc_id"] for d in docs[:-1]]
    for drug, per in meds.items():
        in_newest = per.get(newest["doc_id"])
        in_older = [per[i] for i in older_ids if i in per]
        if in_newest and in_newest.get("stopped"):
            lab = "stopped"
        elif in_newest and not in_older:
            lab = "new_start"
        elif not in_newest and in_older:
            lab = "possible_omission"
        elif len({_norm_dose(m) for m in per.values()}) > 1:
            lab = "dose_differs"
        else:
            lab = "consistent"
        med_labels[drug] = {"label": lab, "status": "supported" if lab == "consistent" else "conflicting",
                            "sources": {k: [v["span"], _norm_dose(v) or v.get("stopped")] for k, v in per.items()}}
    return {"allergy_state": allergy_state,
            "allergy_sources": {d["doc_id"]: [a["text"] for a in d["allergies"]] or [d["nkda"]]
                                for d in docs if d["allergies"] or d["nkda"]},
            "problems": problems, "medications": med_labels}


def build(packet: dict, workers: int = 4) -> dict:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        extracted = list(ex.map(extract_document, packet["documents"]))
    out = label(extracted)
    out["credits"] = sum(int(e["credits"] or 0) for e in extracted)
    out["extracted"] = extracted
    return out
