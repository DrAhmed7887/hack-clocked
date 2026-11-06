"""Seeded generator of synthetic cross-border record packets with planted conflicts and an answer key.

Synthetic only: no real patients, no real names. Labels follow the signed clinical rules (research/EVIDENCE.md):
R2 status (supported / conflicting / not_found), R3 allergy states, R4 medication labels.
Usage: python3 data/generate.py  ->  data/packets/packet_XX.json
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261107
N_PACKETS = 20
OUT = Path(__file__).parent / "packets"

# name, doses (first is the usual one), frequency
DRUGS = [
    ("metformin", ["500 mg", "1000 mg"], "twice daily"),
    ("amlodipine", ["5 mg", "10 mg"], "once daily"),
    ("atorvastatin", ["20 mg", "40 mg"], "at night"),
    ("lisinopril", ["10 mg", "20 mg"], "once daily"),
    ("levothyroxine", ["50 micrograms", "75 micrograms"], "once daily before breakfast"),
    ("omeprazole", ["20 mg", "40 mg"], "once daily"),
    ("bisoprolol", ["2.5 mg", "5 mg"], "once daily"),
    ("warfarin", ["3 mg", "5 mg"], "once daily, dose by INR"),
    ("insulin glargine", ["16 units", "22 units"], "at night"),
    ("salbutamol inhaler", ["100 micrograms, 2 puffs", "100 micrograms, 4 puffs"], "as needed"),
]
PROBLEMS = ["type 2 diabetes", "essential hypertension", "hypothyroidism", "asthma", "atrial fibrillation",
            "gastro-oesophageal reflux disease", "chronic kidney disease stage 3a", "hyperlipidaemia"]
ALLERGENS = [("penicillin", "rash"), ("sulfonamides", "hives"), ("aspirin", "wheeze"), ("latex", "contact dermatitis")]

SETTINGS = [
    ("discharge", "Discharge summary, internal medicine ward, Cairo (translated to English)"),
    ("gp_letter", "GP referral letter, primary care centre, Valencia"),
    ("pharmacy", "Community pharmacy dispensing record, Valencia"),
    ("clinic", "Outpatient clinic note, Alexandria"),
]
MED_LABELS = ["consistent", "dose_differs", "possible_omission", "new_start", "stopped"]
ALLERGY_STATES = ["known", "conflicting", "nkda", "no_info"]


def make_packet(i: int, rng: random.Random) -> dict:
    n_docs = rng.choice([2, 3, 3, 4])
    kinds = rng.sample(SETTINGS, n_docs)
    start = date(2024, 1, 1) + timedelta(days=rng.randint(0, 400))
    dates = sorted(start + timedelta(days=rng.randint(30, 640)) for _ in range(n_docs))
    docs = [{"doc_id": f"D{k + 1}", "kind": kd, "setting": label, "date": d.isoformat(), "lines": []}
            for k, ((kd, label), d) in enumerate(zip(kinds, dates))]
    newest, older = docs[-1], docs[:-1]
    age, sex = rng.randint(34, 82), rng.choice(["female", "male"])

    # Problems: some in every document, one only in an older document (still supported: R2).
    probs = rng.sample(PROBLEMS, rng.randint(2, 4))
    truth_problems = []
    clinical_docs = [d for d in docs if d["kind"] != "pharmacy"] or docs  # a pharmacy record lists no diagnoses
    for p in probs:
        where = clinical_docs if rng.random() < 0.6 else [rng.choice(clinical_docs)]
        for d in where:
            d["lines"].append(("problem", f"Known {p}."))
        truth_problems.append({"name": p, "status": "supported", "sources": [d["doc_id"] for d in where]})
    absent = rng.choice([p for p in PROBLEMS if p not in probs])
    truth_problems.append({"name": absent, "status": "not_found", "sources": [], "note": "decoy: never mentioned"})

    # Allergies (R3, R5, R6).
    state = ALLERGY_STATES[i % 4]
    allergen, reaction = rng.choice(ALLERGENS)
    if state == "known":
        for d in docs:
            d["lines"].append(("allergy", f"Allergy: {allergen} ({reaction})."))
    elif state == "conflicting":
        a, b = rng.sample(docs, 2)
        a["lines"].append(("allergy", f"Allergy: {allergen} ({reaction})."))
        b["lines"].append(("allergy", "No known drug allergies."))
    elif state == "nkda":
        for d in rng.sample(docs, rng.randint(1, n_docs)):
            d["lines"].append(("allergy", "No known drug allergies."))
    truth_allergy = {"state": state, "allergen": allergen if state in ("known", "conflicting") else None,
                     "reaction": reaction if state in ("known", "conflicting") else None}

    # Medications (R4): one of each label where possible, plus extra consistent ones.
    drugs = rng.sample(DRUGS, 5)
    labels = rng.sample(MED_LABELS, 4) + ["consistent"]
    truth_meds = []
    for (name, doses, freq), label in zip(drugs, labels):
        dose = doses[0]
        per_doc = {}
        if label == "consistent":
            for d in docs:
                per_doc[d["doc_id"]] = f"{name} {dose} {freq}"
        elif label == "dose_differs":
            for d in older:
                per_doc[d["doc_id"]] = f"{name} {dose} {freq}"
            per_doc[newest["doc_id"]] = f"{name} {doses[1]} {freq}"
        elif label == "possible_omission":
            for d in older:
                per_doc[d["doc_id"]] = f"{name} {dose} {freq}"
        elif label == "new_start":
            per_doc[newest["doc_id"]] = f"{name} {dose} {freq}"
        elif label == "stopped":
            for d in older:
                per_doc[d["doc_id"]] = f"{name} {dose} {freq}"
            per_doc[newest["doc_id"]] = f"{name} stopped on {newest['date']}"
        for d in docs:
            if d["doc_id"] in per_doc:
                d["lines"].append(("med", f"- {per_doc[d['doc_id']]}"))
        truth_meds.append({"drug": name, "label": label,
                           "status": "conflicting" if label != "consistent" else "supported",
                           "per_doc": per_doc})

    documents = []
    for d in docs:
        body = [f"{d['setting']}", f"Date: {d['date']}", f"Patient: synthetic case P{i:03d}, {age}-year-old {sex}.", ""]
        problem_lines = [t for k, t in d["lines"] if k == "problem"]
        if d["kind"] != "pharmacy":
            body += ["Problems:"] + (problem_lines or ["none recorded."])
        allergy_lines = [t for k, t in d["lines"] if k == "allergy"]
        if allergy_lines:
            body += [""] + allergy_lines
        body += ["", "Medications:"] + ([t for k, t in d["lines"] if k == "med"] or ["- none listed"])
        documents.append({"doc_id": d["doc_id"], "kind": d["kind"], "date": d["date"], "text": "\n".join(body)})

    return {"packet_id": f"P{i:03d}", "seed": SEED, "synthetic": True, "documents": documents,
            "truth": {"problems": truth_problems, "allergy": truth_allergy, "medications": truth_meds}}


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    for i in range(1, N_PACKETS + 1):
        packet = make_packet(i, rng)
        (OUT / f"packet_{i:02d}.json").write_text(json.dumps(packet, indent=2))
    print(f"wrote {N_PACKETS} packets to {OUT}")


if __name__ == "__main__":
    main()
