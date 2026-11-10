# For judges: each criterion and where its evidence is

**Try it (no login, no key):** https://drahmed7887.github.io/hack-clocked/. Start with patient P001. The [method page](https://drahmed7887.github.io/hack-clocked/method.html) explains each step. The site is built from the recorded Clocked responses in `runs/raw/`, so no key reaches the browser.

**Headline result:** the realistic test set has 20 synthetic patients and 61 records, with prescriber shorthand and Spanish GP letters. On it, the final handoff names **all 70 discrepancies** (65 medication, 5 allergy) and **invents no medicine**, and **100/100** medication labels are correct. Clocked Fill named 55 of the 70 in sentences that Clocked Verify confirmed. The physician-signed rules added the other 15: 6 established by comparing records (R7a) and 9 rule-built sentences (R7b) whose quoted words Verify confirmed one record at a time (the absence itself comes from the rules). Each sentence is labelled with how it was established. Sources: `eval/RESULTS_hard.md`, `eval/SUMMARY_hard.md`.

Every number here comes from a script output in `eval/`. The README is the single source for claims; this page only points to them.

## Best Overall App

| Criterion (challenge wording) | Points | Evidence | Where |
|---|---|---|---|
| **Practical usefulness** | 25 | It is for the clinician receiving a patient whose records come from several countries and disagree. Each medication, allergy and problem is labelled (missing from the newest record, dose or timing differs, stopped, new, same in all records) and shown with the exact words from every record. An allergy alert sits on top when records disagree. Conflicts are never resolved for the clinician. Medication-history errors at admission occur in up to 67% of cases (Tam et al., CMAJ 2005). | README "Why", "What a clinician sees"; `research/EVIDENCE.md`; live demo, patient P001 |
| **Quality of the core Clocked integration** | 30 | Clocked does the reading and the checking. Extract copies every fact with exact character positions, and those spans are the quotes on screen. Fill drafts one sentence per discrepancy. Verify checks each sentence against the original records: 9 unsupported sentences were removed from the realistic set's handoffs and are listed. Credits charged when the realistic set was first run live: 474 (Extract), 610 (Fill and Verify), 575 (Protect and Compare). | `src/handoff.py` (`extract_document`), `src/summary.py` (`write_and_verify`), `src/clocked.py`; `eval/RESULTS_hard.md`, `eval/SUMMARY_hard.md`, `eval/CROSSCHECK_hard.md` |
| **Thoughtful use of additional Clocked endpoints** | 15 | Protect runs first as a privacy gate that fails closed: 20/20 packets passed, and any hit other than the synthetic case label stops processing. Compare runs on the raw records as an independent conflict detector. It flagged 25 of the 39 rule-found conflicts, and raised none that no rule explained. Each patient page shows both results under "Independent cross-checks". | `src/crosscheck.py` (`privacy_gate`, `compare_check`); `app/render.py`; `tests/test_crosscheck.py`; `eval/CROSSCHECK_hard.md` |
| **Implementation and user experience** | 20 | The most dangerous changes come first. Each sentence carries a badge saying how it was checked, and every fact shows its source words. The site is static, with no key in the browser. CI runs 29 offline rule tests, checks that the seeded synthetic data rebuilds identically, re-runs all seven evals from the recorded responses, and scans the whole history for secrets. | `app/build_site.py`, `site/`; `.github/workflows/ci.yml`; `tests/`; [demo film, 2:32](https://youtu.be/Bjk8wvfwo-s) |
| **Clear explanation and reproducibility** | 10 | The commands below re-run every number from the recorded responses, with no key and no credits. The 787 recorded responses are committed in `runs/raw/`, and CI re-runs all seven evals from them on every push and fails if any committed result changes. The workflow diagram and the film follow one allergy sentence through Protect, Extract, the rules, Fill and Verify. | "Reproduce" below; README "Run it"; `docs/workflow.svg` |

## Group awards

The challenge counts an endpoint as used meaningfully when "the endpoint's output changes what the application does or shows". Here is what each endpoint's output changes:

| Group | Endpoint | What its output changes |
|---|---|---|
| Decide, Extract, or Fill | Extract | Its medication records (drug, dose, frequency, stopped, line) and character spans are the facts the rules label and the quotes the clinician reads. |
| | Fill | Its sentences become the written handoff, but only after Verify has checked them. |
| Protect, Guard, or Inspect | Protect (pii) | A hit other than the synthetic case label, or an unexpected response, stops the run before any other endpoint sees the record; the site build exits with an error. |
| Verify, Compare, or Rerank | Verify (grounding) | An unsupported sentence is removed from the handoff and listed as removed. Testing Verify led to two rules. A conflict sentence rebuilt by the rules (R7b) is checked one record at a time, because as a whole it reads as "contradicted" by design. An absence is established by comparing records, because a text checker cannot prove that something is missing (R7a). |
| | Compare | Its conflicts are matched against the rules' findings and shown on each patient page; a conflict that no rule explains is listed for the clinician to review. |

| Criterion (challenge wording) | Points | Evidence |
|---|---|---|
| **Depth: how the group's endpoints shape what the application does** | 40 | The table above, plus the per-endpoint results in `eval/` |
| **Breadth: endpoints of the group used meaningfully, 10 each** | 30 | 2 of 3 (Extract, Fill) · 1 of 3 (Protect) · 2 of 3 (Verify, Compare) |
| **Practical usefulness and execution** | 20 | As for Best Overall App above |
| **Clear explanation and reproducibility** | 10 | As for Best Overall App above |

## Limits (from the README)

- Synthetic records only, in English and Spanish, with random drug and problem pairings (`data/DATA_CARD.md`).
- The demo replays recorded Clocked responses. With your own key and an empty `runs/raw/`, the same scripts call Clocked live, and credits are charged.
- Extraction missed 4 of 57 problems on the realistic set (mixed-format lists). They are reported, not hidden.
- Compare found 24 to 25 of the 39 rule-found conflicts on its own. It is a corroborating signal, not the source of the labels.
- Whether Verify accepts a given wording varies from run to run; rules R7a and R7b cover the cases it does not.
- Not yet implemented from the signed rules: immunizations (R1) and an explicit "Not found" status per fact (R2).
- Not a medical device. It does not recommend any drug, dose or action.

## Reproduce (no key, no credits, a few seconds)

```bash
python3 -m unittest discover -s tests -v   # 29 rule tests, offline
python3 eval/score.py 0 hard               # Extract + rules   -> eval/RESULTS_hard.md
python3 eval/score_summary.py hard         # Fill + Verify     -> eval/SUMMARY_hard.md
python3 eval/score_crosscheck.py hard      # Protect + Compare -> eval/CROSSCHECK_hard.md
git status --short eval/                   # prints nothing: the committed results reproduce
```

The eval scripts read the 787 recorded Clocked responses committed in `runs/raw/` and need no key. Use `clean` instead of `hard` for the clean-wording set.
