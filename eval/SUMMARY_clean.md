# Written handoff results, clean set (20 packets)

Produced by `python3 eval/score_summary.py`. Synthetic data only.

- Discrepancies named in the final text: **70/70**
- Generated sentences kept on text evidence (Clocked Verify): **62**
- Sentences kept on record comparison (rule R7a): **5**
- Sentences added by the rules safety net (R7b): **5** (Verify supported 1 of them)
- Generated sentences removed as unsupported: **5**
- Medicines named in the final text that are not in the records: **0**
- Clocked credits (Fill + Verify, as charged when first run): 610

## Not covered


## Removed sentences

- P001: Allergy conflict new: the pharmacy record of 2025-04-17 says 'sulfonamides (hives)' and the GP letter of 2025-12-25 says 'No known drug allergies.
- P005: Allergy conflict: the GP letter of 2025-06-05 says 'latex (contact dermatitis)' and the discharge summary of 2025-12-08 says 'No known drug allergies.
- P009: Allergy conflict new, the discharge summary of 2026-03-26 says 'No known drug allergies.
- P009: Levothyroxine dose differs, the discharge summary of 2026-03-26 says 'levothyroxine 50 micrograms once daily before breakfast' and the clinic note of 2026-06-13 says 'levothyroxine 75 micrograms once daily before breakfast'
- P013: Allergy conflict new: the discharge summary of 2024-04-14 says 'latex (contact dermatitis)' and the GP letter of 2024-04-15 says 'No known drug allergies.
