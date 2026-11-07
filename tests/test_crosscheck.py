"""Offline tests for the Compare matching and the Protect allow-list."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from crosscheck import ALLOWED, match_conflicts  # noqa: E402
from summary import split_attributions  # noqa: E402

HANDOFF = {"allergy_state": "conflicting",
           "medications": {"bisoprolol": {"label": "dose_differs"}, "warfarin": {"label": "possible_omission"},
                           "metformin": {"label": "consistent"}}}


def finding(qa, qb):
    return {"a": {"quote": qa}, "b": {"quote": qb}}


class CompareMatching(unittest.TestCase):
    def test_flags_are_matched_by_short_quotes(self):
        cmp = {"conflicts": [0, 1], "pairs": [
            {"a": "D1", "b": "D2", "conflicts": [finding("- bisoprolol 2.5mg o.d.", "x" * 500)]},
            {"a": "D1", "b": "D3", "conflicts": [finding("Allergies: sulfonamides (hives)", "Sin alergias conocidas.")]}]}
        out = match_conflicts(cmp, HANDOFF)
        self.assertEqual(out["also_flagged_by_compare"], ["allergy", "bisoprolol"])
        self.assertEqual(out["compare_only"], [])

    def test_whole_document_quote_does_not_match_everything(self):
        cmp = {"conflicts": [0], "pairs": [{"a": "D1", "b": "D2", "conflicts": [finding("lisinopril 10 mg", "bisoprolol " * 40)]}]}
        out = match_conflicts(cmp, HANDOFF)
        self.assertEqual(out["also_flagged_by_compare"], [])
        self.assertEqual(len(out["compare_only"]), 1)  # shown to the clinician, not dropped


class ProtectAllowList(unittest.TestCase):
    def test_only_the_synthetic_label_is_allowed(self):
        self.assertTrue(ALLOWED.match("caso sintético P001"))
        self.assertTrue(ALLOWED.match("synthetic case P020"))
        self.assertTrue(ALLOWED.match("P002"))
        self.assertFalse(ALLOWED.match("X12345678"))
        self.assertFalse(ALLOWED.match("Ahmed Example"))
        self.assertFalse(ALLOWED.match("synthetic case P001, Maria Lopez"))


class AttributionSplit(unittest.TestCase):
    def test_conflict_sentence_is_verified_one_record_at_a_time(self):
        s = ("Allergy conflict: the pharmacy record of 2025-04-17 says 'sulfonamides (hives)'; "
             "the GP letter of 2025-12-25 says 'Sin alergias medicamentosas conocidas.'.")
        parts = split_attributions(s)
        self.assertEqual(len(parts), 2)
        self.assertIn("pharmacy record of 2025-04-17 says 'sulfonamides (hives)'", parts[0])


if __name__ == "__main__":
    unittest.main()
