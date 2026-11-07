# Evidence-Linked Clinical Handoff

**When a patient arrives with records from several countries, the receiving clinician needs to know which facts are supported, which conflict, and which are missing.** This tool reads every record, labels each medication, allergy and problem, quotes the exact source words, and writes a short handoff drafted by Clocked Fill and checked sentence by sentence by Clocked Verify. Sentences the checker cannot confirm are removed; absences and gaps are filled from fixed rules and labelled as such.

Built for the Clocked Build Challenge 2026 by a physician (12 years in clinical practice) studying health informatics. **Synthetic records only. Decision support for clinicians, not a diagnosis or a prescription.**

## Why
- Medication history errors at hospital admission occur in up to 67% of cases ([Tam et al., CMAJ 2005](https://doi.org/10.1503/cmaj.045311)).
- AI summaries of outside-facility records: thoroughness was rated low in 45% and 40% contained errors, about half of them treatment-impacting ([Park et al., Ann Surg Oncol 2026](https://doi.org/10.1245/s10434-026-20170-w)).
- A structured handoff programme cut medical errors by 23% ([Starmer et al., NEJM 2014](https://doi.org/10.1056/NEJMsa1405556)).

All evidence, with exact quotes and dates checked: [`research/EVIDENCE.md`](research/EVIDENCE.md).

## What a clinician sees
1. An **allergy alert** at the top when records disagree, quoting both records.
2. A **written handoff**: one sentence per discrepancy, leading with what changed ("Warfarin missing from the newest record: …"), each with a badge saying how it was checked.
3. **Medications**, most dangerous first: *missing from newest record*, *dose or timing differs*, *stopped*, *new*, *same in all records*, each with every record's exact words.
4. **Problems** and the **source records**.

Conflicts are never resolved for the clinician, and the newest record is never assumed to be right.

## How Clocked is used
| Step | Clocked endpoint | What it does here |
|---|---|---|
| 1 | **Extract** (`/clocked/extract`) | Copies problems, allergies and each medication line (as records with `drug`, `dose`, `frequency`, `stopped`, `line`) from every document, with exact character positions. |
| 2 | (fixed rules) | Normalise prescriber shorthand and Spanish (BD = cada 12 horas = twice daily; 2,5 mg = 2.5 mg; metformina = metformin), then label every fact. Unrecognised wording is compared as written, never assumed equal. **No model decides a label.** |
| 3 | **Fill** (`/clocked/fill`, `generate`) | Drafts one sentence per discrepancy, quoting the records. |
| 4 | **Verify** (`/clocked/grounding`) | Checks each drafted sentence against the **original** records. Unsupported sentences are removed and shown. |

Two safety rules came out of testing:
- **Absences are established by comparison (R7a).** Verify removed the true sentence "warfarin is missing from the newest record" as *not stated*: a text checker cannot prove that something is missing. Such sentences are kept, marked "established by comparing records".
- **A rules safety net (R7b).** Any discrepancy the draft leaves out is added from the rules as a sentence built only from verbatim quotes, with Verify's verdict shown beside it.

The clinical rules (R1–R9, R7a, R7b) were reviewed and signed by the physician author before they became code.

## Results (synthetic test sets, produced by the scripts in `eval/`)
Two sets of 20 synthetic patients (61 records): **clean** wording, and **realistic** wording with prescriber shorthand, "NKDA", "History of …" lines and every Valencia GP letter in Spanish. Same answer keys.

| | Clean | Realistic |
|---|---|---|
| Allergy state correct | 20/20 | 20/20 |
| Allergy conflicts flagged | 5/5 | 5/5 |
| Medication labels correct | 100/100 | 100/100 |
| Medication discrepancies flagged | 65/65 | 65/65 |
| Problems found | 57/57 | 53/57 |
| Invented medicines or problems | 0 | 0 |
| Discrepancies named by Fill sentences that Verify confirmed | 61/70 | 55/70 |
| Discrepancies named in the final written handoff (after rules R7a/R7b) | 70/70 | 70/70 |
| Medicines named in the handoff that are not in the records | 0 | 0 |

Before the shorthand/Spanish normalisation, medication labels on the realistic set were 54/100. The 4 missed problems are extraction misses on mixed-format lists; they are reported, not hidden. These numbers describe this synthetic test set, not real-world accuracy.

## Run it
```bash
python3 -m unittest discover -s tests -v        # rule tests, offline
python3 data/generate.py && python3 data/make_hard.py   # synthetic data (seeded)
export CLOCKED_API_KEY=...                       # your own key; never commit it
python3 eval/score.py 0 hard                     # Extract + rules, scored
python3 eval/score_summary.py hard               # Fill + Verify, scored
python3 app/build_site.py                        # static site in site/
```
Standard library only (Python 3.9+). The demo site is plain HTML built from recorded Clocked responses: no API key reaches the browser.

## Limits
- Synthetic, English and Spanish records only; drug and problem pairings are random (see [`data/DATA_CARD.md`](data/DATA_CARD.md)).
- The shorthand and Spanish vocabulary is a fixed list for this data set; unknown terms are shown as written, never guessed.
- Not yet implemented from the signed rules: immunizations (R1, recommended section) and an explicit "Not found" status per fact (R2); problems are shown only when a record states them.
- Rule-built sentences (R7b) are made from verbatim quotes, but Clocked Verify confirmed only some of them (3 of 9 on the realistic set); the page shows each verdict.
- Not a medical device. It does not recommend any drug, dose or action.

## Licence
MIT. Evidence summaries cite their sources; Clocked is a product of Rezolve.ai.
