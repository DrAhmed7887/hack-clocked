"""Regression tests for the 7 Nov independent review (each failed before its fix)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import normalize as nz  # noqa: E402
from handoff import label  # noqa: E402
from test_rules import doc  # noqa: E402


def same(a, b, drug="x"):
    return nz.regimen(a, drug) == nz.regimen(b, drug)


class DoseParsing(unittest.TestCase):
    def test_spanish_decimal_comma(self):  # finding 2
        self.assertFalse(same("bisoprolol 2,5 mg una vez al día", "bisoprolol 5 mg OD", "bisoprolol"))
        self.assertTrue(same("bisoprolol 2,5 mg una vez al día", "bisoprolol 2.5 mg OD", "bisoprolol"))

    def test_gram_and_other_units(self):  # finding 1
        self.assertFalse(same("metformin 1 g daily", "metformin 2 g daily", "metformin"))
        self.assertFalse(same("lactulose 10 ml BD", "lactulose 15 ml BD", "lactulose"))

    def test_number_without_known_unit_is_not_ignored(self):  # finding 1 fallback
        self.assertFalse(same("vitamin d 1000 daily", "vitamin d 2000 daily", "vitamin d"))


class FrequencyParsing(unittest.TestCase):  # finding 3
    def test_three_times_daily_is_not_once_daily(self):
        self.assertFalse(same("x 500 mg three times daily", "x 500 mg once daily"))
        self.assertTrue(same("x 500 mg TDS", "x 500 mg cada 8 horas"))

    def test_morning_vs_night_differ(self):
        self.assertFalse(same("x 5 mg once daily in the morning", "x 5 mg once daily at night"))

    def test_word_on_is_not_at_night(self):
        self.assertFalse(same("x 5 mg started on 2025-01-02", "x 5 mg at night"))
        self.assertTrue(same("atorvastatin 20 mg ON", "atorvastatin 20 mg nocte", "atorvastatin"))

    def test_two_unmapped_frequencies_do_not_silently_match(self):
        self.assertFalse(same("x 5 mg every other Tuesday", "x 5 mg with lunch"))

    def test_known_equivalents_still_match(self):
        self.assertTrue(same("levothyroxine 50 mcg mane, before food", "levotiroxina 50 microgramos una vez al día en ayunas",
                             "levothyroxine"))
        self.assertTrue(same("warfarin 3 mg once daily, dose by INR", "warfarina 3 mg una vez al día según INR", "warfarin"))


class RecordLogic(unittest.TestCase):
    def test_two_lines_of_same_drug_in_one_record_are_both_kept(self):  # finding 4
        out = label([doc("A", "2024-01-01", meds=[("metformin", "500 mg mane"), ("metformin", "1000 mg nocte")]),
                     doc("B", "2025-01-01", meds=[("metformin", "1000 mg nocte")])])
        self.assertEqual(out["medications"]["metformin"]["label"], "dose_differs")

    def test_stop_in_older_record_is_reported_as_stopped(self):  # finding 9
        out = label([doc("A", "2024-01-01", meds=[("omeprazole", "20 mg OD")]),
                     doc("B", "2024-06-01", meds=[("omeprazole", "retirado el 2024-06-01")]),
                     doc("C", "2025-01-01")])
        self.assertEqual(out["medications"]["omeprazole"]["label"], "stopped")

    def test_non_iso_date_fails_loudly(self):  # finding 8
        with self.assertRaises(ValueError):
            label([doc("A", "07/11/2026"), doc("B", "2025-01-01")])


if __name__ == "__main__":
    unittest.main()
