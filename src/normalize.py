"""Deterministic normalisation of extracted spans before comparison (no model involved).

The vocabulary is a fixed demo list covering the synthetic data set (English, Spanish, prescriber shorthand).
Unknown terms pass through unchanged and are shown as written; they are never guessed. Unrecognised frequency
wording is compared as written, so two different unknown phrasings never silently count as the same regimen.
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
# Frequency phrases -> tags. Each phrase is consumed once, longest first, so "three times daily" cannot also match "daily".
FREQUENCY = {
    "twice daily": {"2/day"}, "twice a day": {"2/day"}, "b.i.d.": {"2/day"}, "bid": {"2/day"}, "bd": {"2/day"},
    "cada 12 horas": {"2/day"}, "every 12 hours": {"2/day"},
    "three times daily": {"3/day"}, "three times a day": {"3/day"}, "t.d.s.": {"3/day"}, "tds": {"3/day"},
    "tid": {"3/day"}, "cada 8 horas": {"3/day"}, "every 8 hours": {"3/day"},
    "four times daily": {"4/day"}, "q.d.s.": {"4/day"}, "qds": {"4/day"}, "qid": {"4/day"},
    "cada 6 horas": {"4/day"}, "every 6 hours": {"4/day"},
    "once daily": {"1/day"}, "once a day": {"1/day"}, "o.d.": {"1/day"}, "od": {"1/day"}, "daily": {"1/day"},
    "una vez al día": {"1/day"},
    "at night": {"night"}, "nocte": {"night"}, "por la noche": {"night"},
    "in the morning": {"morning"}, "mane": {"morning"}, "por la mañana": {"morning"},
    "before breakfast": {"morning", "fasting"}, "en ayunas": {"morning", "fasting"}, "before food": {"fasting"},
    "dose by inr": {"by INR"}, "as per inr": {"by INR"}, "según inr": {"by INR"},
    "as needed": {"as needed"}, "prn": {"as needed"}, "when required": {"as needed"}, "a demanda": {"as needed"},
    "once weekly": {"1/week"}, "weekly": {"1/week"}, "semanal": {"1/week"},
    "on alternate days": {"alternate days"}, "alternate days": {"alternate days"}, "días alternos": {"alternate days"},
}
UNIT = r"(micrograms?|microgramos|mcg|µg|mg|g|gramos|ml|iu|ui|units?|unidades|puffs?|inhalaciones|tablets?|comprimidos?|%)"
UNIT_NORM = {"microgram": "mcg", "micrograms": "mcg", "microgramos": "mcg", "mcg": "mcg", "µg": "mcg", "mg": "mg",
             "g": "g", "gramos": "g", "ml": "ml", "iu": "IU", "ui": "IU", "unit": "units", "units": "units",
             "unidades": "units", "puff": "puffs", "puffs": "puffs", "inhalaciones": "puffs", "tablet": "tablets",
             "tablets": "tablets", "comprimido": "tablets", "comprimidos": "tablets", "%": "%"}
STOP_WORDS = ("stopped", "suspendido", "suspendida", "discontinued", "suspended", "retirado", "retirada",
              "interrumpido", "se suspende", "stop ")
FILLER = {"and", "y", "with", "con", "take", "tomar", "tablet", "tablets", "dose", "dosis", "of", "de", "the", "el", "la", "as", "per"}


def drug(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").strip().lower())
    return DRUG_SYNONYMS.get(n, n)


def problem(name: str) -> str:
    n = re.sub(r"^(known|history of|antecedente de)\s+", "", (name or "").strip().lower()).strip(" .-")
    return PROBLEM_SYNONYMS.get(n, n)


def _number(raw: str) -> str:
    n = raw.replace(",", ".")
    return n.rstrip("0").rstrip(".") if "." in n else n


def regimen(line: str, drug_name: str) -> str:
    """'metformin 500mg bd' -> '500 mg | 2/day'. Strength and frequency are compared, wording is not."""
    original = line or ""
    night_on = bool(re.search(r"(?<![A-Za-z])ON(?![A-Za-z])", original))  # UK shorthand, capitals only
    text = original.lower()
    for raw in sorted([drug_name] + [k for k, v in DRUG_SYNONYMS.items() if v == drug_name], key=len, reverse=True):
        text = text.replace(raw, " ")
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)  # dates are not doses
    amounts = []

    def take_amount(m):
        amounts.append(f"{_number(m.group(1))} {UNIT_NORM[m.group(2)]}")
        return " "
    text = re.sub(rf"(\d+(?:[.,]\d+)?)\s*{UNIT}(?![a-z])", take_amount, text)
    tags = set()
    for phrase in sorted(FREQUENCY, key=len, reverse=True):
        pattern = rf"(?<![a-z]){re.escape(phrase)}(?![a-z])"
        if re.search(pattern, text):
            tags |= FREQUENCY[phrase]
            text = re.sub(pattern, " ", text)
    # Bare numbers left after units and frequency phrases ("cada 12 horas") are kept, never dropped (finding 1).
    text = re.sub(r"\d+(?:[.,]\d+)?", lambda m: amounts.append(f"{_number(m.group(0))} ?") or " ", text)
    if night_on:
        tags.add("night")
    if tags & {"night", "morning"} and not tags & {"1/day", "2/day", "3/day", "4/day", "1/week", "alternate days"}:
        tags.add("1/day")  # a single named time of day means once daily
    leftover = " ".join(w for w in re.findall(r"[a-záéíóúñü]+", text) if w not in FILLER and w != "on")
    freq = " + ".join(sorted(tags)) if tags else (f"unrecognised: {leftover}" if leftover else "")
    return f"{' + '.join(amounts)} | {freq}".strip()


def is_stop(text: str) -> bool:
    t = f"{(text or '').lower()} "
    return any(w in t for w in STOP_WORDS)
