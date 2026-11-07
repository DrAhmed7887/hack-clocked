"""Offline tests for the Compare matching and the Protect allow-list."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from crosscheck import ALLOWED, match_conflicts  # noqa: E402
from summary import _items  # noqa: E402

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


class StructuralClaims(unittest.TestCase):  # claims are built from quote lists, never parsed back (PR#2 #8)
    def test_one_claim_per_record_even_with_apostrophes(self):
        docs = [{"doc_id": "A", "kind": "pharmacy", "date": "2025-04-17", "text": "it's fine; take 5 mg"},
                {"doc_id": "B", "kind": "gp_letter", "date": "2025-12-25", "text": "x 10 mg"}]
        h = {"allergy_state": "known", "allergy_sources": {},
             "medications": {"x": {"label": "dose_differs", "sources": {"A": {"spans": [[0, 20]]}, "B": {"spans": [[0, 7]]}}}}}
        items, claims = _items(h, docs)
        self.assertEqual(len(claims["x"]), 2)
        self.assertIn("it's fine; take 5 mg", claims["x"][0])


class CompareShapes(unittest.TestCase):
    def test_value_conflict_on_an_omitted_drug_is_not_hidden(self):  # PR#2 #4
        h = {"allergy_state": "known", "medications": {"warfarin": {"label": "possible_omission"}}}
        cmp = {"conflicts": [0], "pairs": [{"a": "D1", "b": "D2", "conflicts": [finding("warfarin 3 mg OD", "warfarin 5 mg OD")]}]}
        self.assertEqual(len(match_conflicts(cmp, h)["compare_only"]), 1)

    def test_bad_shape_fails_loudly(self):  # PR#2 #5
        with self.assertRaises(RuntimeError):
            match_conflicts({"conflicts": [0]}, {"allergy_state": "known", "medications": {}})


if __name__ == "__main__":
    unittest.main()


class GateFailsClosed(unittest.TestCase):  # PR#2 #1, #2 (no API call: Protect is simulated)
    def run_gate(self, response):
        import crosscheck
        real = crosscheck.call
        crosscheck.call = lambda endpoint, payload: response
        try:
            return crosscheck.privacy_gate({"documents": [{"doc_id": "D1", "text": "x"}]})
        finally:
            crosscheck.call = real

    def test_malformed_response_does_not_pass(self):
        self.assertFalse(self.run_gate({"error": "oops"})["passed"])

    def test_label_value_with_wrong_type_does_not_pass(self):
        self.assertFalse(self.run_gate({"entities": [{"type": "phone", "value": "P001"}]})["passed"])
        self.assertTrue(self.run_gate({"entities": [{"type": "person", "value": "caso sintético P001"}]})["passed"])
