# Written handoff results, hard set (20 packets)

Produced by `python3 eval/score_summary.py`. Synthetic data only.

- Discrepancies named in the final text: **70/70**
- Discrepancies named by Fill sentences that Verify supported (before rules R7a/R7b): **55/70**
- Generated sentences kept on text evidence (Clocked Verify): **57**
- Sentences kept on record comparison (rule R7a): **6**
- Sentences added by the rules safety net (R7b): **9** (Verify supported 9 of them)
- Generated sentences removed as unsupported: **9**
- Medicines named in the final text that are not in the records: **0**
- Clocked credits (Fill + Verify, as charged when first run): 613

## Not covered


## Removed sentences

- P001: Allergy conflict new: the pharmacy record of 2025-04-17 says 'sulfonamides (hives)' and the GP letter of 2025-12-25 says 'Sin alergias medicamentosas conocidas.
- P004: Metformin dose differs: 'metformin 500 mg b.i.d.' from the pharmacy record of 2025-02-15 and 'metformina 1000 mg cada 12 horas' from the GP letter of 2026-03-16
- P005: Allergy conflict dose differs: the GP letter of 2025-06-05 says 'látex (dermatitis de contacto)' and the discharge summary of 2025-12-08 says 'nil known.
- P006: Omeprazole dose differs, 'omeprazole 20mg OD' from the discharge summary of 2025-07-08, 'omeprazole 20 mg o.d.' from the pharmacy record of 2025-10-10, and 'omeprazol 40 mg una vez al día' from the GP letter of 2025-12-03
- P009: Levothyroxine dose differs: the discharge summary of 2026-03-26 says 'levothyroxine 50 micrograms mane, before food' and the clinic note of 2026-06-13 says 'levothyroxine 75 mcg OD before breakfast'
- P012: Lisinopril dose differs, 'lisinopril 10mg daily' from the discharge summary of 2024-06-06, 'lisinopril 10mg OD' from the clinic note of 2024-09-16, and 'lisinopril 20mg OD' from the pharmacy record of 2025-12-01.
- P013: Allergy conflict new: the discharge summary of 2024-04-14 says 'latex - causes contact dermatitis' and the GP letter of 2024-04-15 says 'Sin alergias medicamentosas conocidas.
- P019: Atorvastatin dose differs: 'atorvastatin 20mg ON' from the discharge summary of 2024-12-09, 'atorvastatin 20mg nocte' from the pharmacy record of 2025-05-15, and 'atorvastatina 40 mg por la noche' from the GP letter of 2025-07-20.
- P020: Levothyroxine dose differs, 'levothyroxine 50 mcg mane, before food' from the clinic note of 2025-03-19, 'levotiroxina 50 microgramos una vez al día en ayunas' from the GP letter of 2025-11-01, and 'levothyroxine 75 mcg OD before breakfast' from the discharge summary of 2025-12-19.
