"""Hard test set: same answer keys as data/packets/, realistic wording (seeded).

- Prescriber shorthand (BD, OD, nocte, PRN), dose formatting (500mg, mcg).
- Allergy phrasing variants and "NKDA".
- Valencia GP letters rewritten in Spanish (drug, problem and allergy names, frequencies).
The truth block is copied unchanged: the wording changes, the facts do not.
Usage: python3 data/make_hard.py -> data/packets_hard/
"""
import json
import random
import re
from pathlib import Path

SEED = 20261108
SRC = Path(__file__).parent / "packets"
OUT = Path(__file__).parent / "packets_hard"

FREQ_EN = {"twice daily": ["BD", "bd", "b.i.d."], "once daily before breakfast": ["OD before breakfast", "mane, before food"],
           "once daily, dose by INR": ["OD as per INR"], "once daily": ["OD", "daily", "o.d."],
           "at night": ["nocte", "ON"], "as needed": ["PRN", "when required"]}
FREQ_ES = {"twice daily": "cada 12 horas", "once daily before breakfast": "una vez al día en ayunas",
           "once daily, dose by INR": "una vez al día según INR", "once daily": "una vez al día",
           "at night": "por la noche", "as needed": "a demanda"}
DRUG_ES = {"metformin": "metformina", "amlodipine": "amlodipino", "atorvastatin": "atorvastatina",
           "lisinopril": "lisinopril", "levothyroxine": "levotiroxina", "omeprazole": "omeprazol",
           "bisoprolol": "bisoprolol", "warfarin": "warfarina", "insulin glargine": "insulina glargina",
           "salbutamol inhaler": "salbutamol inhalador"}
PROBLEM_ES = {"type 2 diabetes": "diabetes mellitus tipo 2", "essential hypertension": "hipertensión arterial esencial",
              "hypothyroidism": "hipotiroidismo", "asthma": "asma", "atrial fibrillation": "fibrilación auricular",
              "gastro-oesophageal reflux disease": "enfermedad por reflujo gastroesofágico",
              "chronic kidney disease stage 3a": "enfermedad renal crónica estadio 3a", "hyperlipidaemia": "hiperlipidemia"}
ALLERGEN_ES = {"penicillin": "penicilina", "sulfonamides": "sulfamidas", "aspirin": "ácido acetilsalicílico",
               "latex": "látex"}
REACTION_ES = {"rash": "exantema", "hives": "urticaria", "wheeze": "broncoespasmo", "contact dermatitis": "dermatitis de contacto"}


def english_messy(text: str, rng: random.Random) -> str:
    out = []
    for line in text.split("\n"):
        if line.startswith("- "):
            line = re.sub(r"(\d) mg", r"\1mg", line) if rng.random() < 0.6 else line
            line = line.replace("micrograms", "mcg") if rng.random() < 0.6 else line
            for long, shorts in FREQ_EN.items():
                if long in line:
                    line = line.replace(long, rng.choice(shorts))
                    break
        elif line.startswith("Allergy: "):
            m = re.match(r"Allergy: (.+) \((.+)\)\.", line)
            if m:
                line = rng.choice([f"Allergic to {m[1]} - causes {m[2]}.", f"Allergies: {m[1]} ({m[2]})", line])
        elif line == "No known drug allergies.":
            line = rng.choice(["NKDA", "Allergies: nil known.", line])
        elif line.startswith("Known "):
            line = rng.choice([line, line.replace("Known ", "History of "), "- " + line[6:].rstrip(".")])
        out.append(line)
    return "\n".join(out)


def spanish(text: str) -> str:
    out = []
    for line in text.split("\n"):
        if line.startswith("GP referral letter"):
            line = "Informe de derivación, centro de atención primaria, Valencia"
        elif line.startswith("Date: "):
            line = "Fecha: " + line[6:]
        elif line.startswith("Patient: "):
            line = (line.replace("Patient: synthetic case", "Paciente: caso sintético")
                    .replace("-year-old female", " años, mujer").replace("-year-old male", " años, varón"))
        elif line == "Problems:":
            line = "Antecedentes:"
        elif line.startswith("Known "):
            line = "- " + PROBLEM_ES.get(line[6:].rstrip("."), line[6:].rstrip("."))
        elif line == "none recorded.":
            line = "sin antecedentes registrados."
        elif line == "No known drug allergies.":
            line = "Sin alergias medicamentosas conocidas."
        elif line.startswith("Allergy: "):
            m = re.match(r"Allergy: (.+) \((.+)\)\.", line)
            line = f"Alergia: {ALLERGEN_ES.get(m[1], m[1])} ({REACTION_ES.get(m[2], m[2])})." if m else line
        elif line == "Medications:":
            line = "Tratamiento:"
        elif line.startswith("- "):
            body = line[2:]
            for en, es in sorted(DRUG_ES.items(), key=lambda kv: -len(kv[0])):
                if body.startswith(en):
                    body = es + body[len(en):]
                    break
            for en, es in FREQ_ES.items():
                body = body.replace(en, es)
            body = body.replace("micrograms", "microgramos").replace("units", "unidades").replace("puffs", "inhalaciones")
            body = re.sub(r"stopped on (\S+)", r"suspendido el \1", body)
            line = "- " + body
        out.append(line)
    return "\n".join(out)


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.glob("packet_*.json")):
        p = json.loads(f.read_text())
        for d in p["documents"]:
            d["text"] = spanish(d["text"]) if d["kind"] == "gp_letter" else english_messy(d["text"], rng)
        p["variant"] = "hard"
        (OUT / f.name).write_text(json.dumps(p, indent=2, ensure_ascii=False))
    print(f"wrote {len(list(OUT.glob('packet_*.json')))} hard packets to {OUT}")


if __name__ == "__main__":
    main()
