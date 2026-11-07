"""Offline tests of the signed clinical rules (no API calls). Run: python3 -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import normalize as nz  # noqa: E402
from handoff import label  # noqa: E402


def doc(doc_id, date, meds=(), allergies=(), nkda=None, problems=()):
    return {"doc_id": doc_id, "date": date, "kind": "clinic", "nkda": nkda,
            "allergies": [{"text": a, "span": [0, 1]} for a in allergies],
            "problems": [{"name": nz.problem(p), "span": [0, 1]} for p in problems],
            "medications": [{"drug": nz.drug(d), "line": f"{d} {rest}", "dose": None, "frequency": None,
                             "stopped": rest if nz.is_stop(rest) else None, "span": [0, 1]} for d, rest in meds]}


class AllergyRules(unittest.TestCase):  # R3, R5, R6
    def test_conflict_when_one_record_lists_allergy_and_another_says_none(self):
        out = label([doc("A", "2025-01-01", allergies=["penicillin (rash)"]), doc("B", "2025-06-01", nkda="NKDA")])
        self.assertEqual(out["allergy_state"], "conflicting")

    def test_no_information_is_not_no_allergies(self):
        self.assertEqual(label([doc("A", "2025-01-01"), doc("B", "2025-02-01")])["allergy_state"], "no_info")
        self.assertEqual(label([doc("A", "2025-01-01", nkda="No known drug allergies.")])["allergy_state"], "nkda")


class MedicationRules(unittest.TestCase):  # R4, R5, R9
    def lab(self, older, newest):
        out = label([doc("A", "2024-01-01", meds=older), doc("B", "2025-01-01", meds=newest)])
        return {k: v["label"] for k, v in out["medications"].items()}

    def test_shorthand_and_spanish_are_the_same_regimen(self):
        self.assertEqual(self.lab([("metformin", "500 mg twice daily")], [("metformina", "500 mg cada 12 horas")]),
                         {"metformin": "consistent"})
        self.assertEqual(self.lab([("atorvastatin", "20mg nocte")], [("atorvastatin", "20 mg at night")]),
                         {"atorvastatin": "consistent"})

    def test_dose_change_is_flagged_and_not_resolved(self):
        self.assertEqual(self.lab([("bisoprolol", "2.5 mg OD")], [("bisoprolol", "5 mg una vez al día")]),
                         {"bisoprolol": "dose_differs"})

    def test_frequency_change_is_flagged(self):
        self.assertEqual(self.lab([("metformin", "500 mg BD")], [("metformin", "500 mg OD")]), {"metformin": "dose_differs"})

    def test_missing_from_newest_is_possible_omission(self):
        self.assertEqual(self.lab([("warfarin", "3 mg OD as per INR")], []), {"warfarin": "possible_omission"})

    def test_new_and_stopped(self):
        self.assertEqual(self.lab([], [("omeprazole", "20 mg OD")]), {"omeprazole": "new_start"})
        self.assertEqual(self.lab([("omeprazole", "20 mg OD")], [("omeprazol", "suspendido el 2025-01-01")]),
                         {"omeprazole": "stopped"})

    def test_newest_record_is_not_assumed_correct(self):
        out = label([doc("A", "2024-01-01", meds=[("bisoprolol", "2.5 mg OD")]),
                     doc("B", "2025-01-01", meds=[("bisoprolol", "5 mg OD")])])
        self.assertEqual(set(out["medications"]["bisoprolol"]["sources"]), {"A", "B"})  # both versions kept


class Normalisation(unittest.TestCase):  # R9: unknown terms pass through, never guessed
    def test_unknown_drug_passes_through(self):
        self.assertEqual(nz.drug("Zyxolan"), "zyxolan")

    def test_problem_prefixes_and_spanish(self):
        self.assertEqual(nz.problem("History of asthma."), "asthma")
        self.assertEqual(nz.problem("fibrilación auricular"), "atrial fibrillation")


if __name__ == "__main__":
    unittest.main()
