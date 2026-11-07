# Written handoff results, hard set (20 packets)

Produced by `python3 eval/score_summary.py`. Synthetic data only.

- Discrepancies named in the final text: **70/70**
- Generated sentences kept on text evidence (Clocked Verify): **63**
- Sentences kept on record comparison (rule R7a): **5**
- Sentences added by the rules safety net (R7b): **5** (Verify supported 1 of them)
- Generated sentences removed as unsupported: **4**
- Medicines named in the final text that are not in the records: **0**
- Clocked credits (Fill + Verify, as charged when first run): 638

## Not covered


## Removed sentences

- P004: The pharmacy record of 2025-02-15 states 'metformin 500 mg b.i.d.', whereas the GP letter of 2026-03-16 states 'metformina 1000 mg cada 12 horas'
- P012: The discharge summary of 2024-06-06 says 'lisinopril 10mg daily', the clinic note of 2024-09-16 says 'lisinopril 10mg OD', and the pharmacy record of 2025-12-01 says 'lisinopril 20mg OD'.
- P018: The pharmacy record of 2025-05-30 says 'warfarin 3mg OD as per INR' and the GP letter of 2025-11-29 says 'warfarina 5 mg una vez al día según INR'
- P019: The discharge summary of 2024-12-09 says 'atorvastatin 20mg ON', the pharmacy record of 2025-05-15 says 'atorvastatin 20mg nocte', and the GP letter of 2025-07-20 says 'atorvastatina 40 mg por la noche'.
