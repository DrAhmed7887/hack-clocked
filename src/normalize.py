"""Deterministic normalisation of extracted spans before comparison (no model involved).

The vocabulary is a fixed demo list covering the synthetic data set (English, Spanish, prescriber shorthand).
Unknown terms pass through unchanged and are shown as written; they are never guessed.
Shorthand meanings are standard prescribing abbreviations, signed off by Ahmed as rule R9 (EVIDENCE.md).
"""
import re

DRUG_SYNONYMS = {
    "metformina": "metformin", "amlodipino": "amlodipine", "atorvastatina": "atorvastatin",
    "levotiroxina": "levothyroxine", "omeprazol": "omeprazole", "warfarina": "warfarin",
    "insulina glargina": "insulin glargine", "salbutamol inhalador": "salbutamol inhaler",
    "salbutamol": "salbutamol inhaler", "salbutamol inhaler": "salbutamol inhaler",
}
PROBLEM_SYNONYMS = {
    "diabetes mellitus tipo 2": "type 2 diabetes", "hipertensión arterial esencial": "essential hypertension",
    "hipotiroidismo": "hypothyroidism", "asma": "asthma", "fibrilación auricular": "atrial fibrillation",
    "enfermedad por reflujo gastroesofágico": "gastro-oesophageal reflux disease",
    "enfermedad renal crónica estadio 3a": "chronic kidney disease stage 3a", "hiperlipidemia": "hyperlipidaemia",
}
# Frequency phrases -> one meaning. Longest phrases are tried first.
FREQUENCY = {
    "twice daily": "2/day", "b.i.d.": "2/day", "bid": "2/day", "bd": "2/day", "cada 12 horas": "2/day",
    "once daily before breakfast": "1/day morning fasting", "od before breakfast": "1/day morning fasting",
    "mane, before food": "1/day morning fasting", "una vez al día en ayunas": "1/day morning fasting",
    "once daily, dose by inr": "1/day by INR", "od as per inr": "1/day by INR", "una vez al día según inr": "1/day by INR",
    "once daily": "1/day", "o.d.": "1/day", "od": "1/day", "daily": "1/day", "una vez al día": "1/day",
    "at night": "1/day night", "nocte": "1/day night", "on": "1/day night", "por la noche": "1/day night",
    "as needed": "as needed", "prn": "as needed", "when required": "as needed", "a demanda": "as needed",
}
UNITS = {"micrograms": "mcg", "microgramos": "mcg", "mcg": "mcg", "mg": "mg", "units": "units", "unidades": "units",
         "puffs": "puffs", "inhalaciones": "puffs"}
STOP_WORDS = ("stopped", "suspendido", "discontinued", "suspended")


def drug(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").strip().lower())
    return DRUG_SYNONYMS.get(n, n)


def problem(name: str) -> str:
    n = re.sub(r"^(known|history of|antecedente de)\s+", "", (name or "").strip().lower()).strip(" .-")
    return PROBLEM_SYNONYMS.get(n, n)


def regimen(line: str, drug_name: str) -> str:
    """'metformin 500mg bd' -> '500 mg | 2/day'. Strengths and frequency are compared, wording is not."""
    text = (line or "").lower()
    for raw in sorted([drug_name] + [k for k, v in DRUG_SYNONYMS.items() if v == drug_name], key=len, reverse=True):
        text = text.replace(raw, " ")
    amounts = [f"{num} {UNITS[unit]}" for num, unit in
               re.findall(r"(\d+(?:\.\d+)?)\s*(micrograms|microgramos|mcg|mg|units|unidades|puffs|inhalaciones)\b", text)]
    freq = ""
    for phrase in sorted(FREQUENCY, key=len, reverse=True):
        if re.search(rf"(?<![a-z]){re.escape(phrase)}(?![a-z])", text):
            freq = FREQUENCY[phrase]
            break
    return f"{' + '.join(amounts)} | {freq}".strip()


def is_stop(text: str) -> bool:
    return any(w in (text or "").lower() for w in STOP_WORDS)
