# Cross-check results, hard set (20 packets)

Produced by `python3 eval/score_crosscheck.py`. Synthetic data only.

- Privacy gate (Clocked Protect) passed: **20/20** packets
- Rule-found dose/stop/allergy conflicts also flagged by Clocked Compare: **25/39**
- Compare conflicts that no rule explained (shown to the clinician for review): **0**
- Clocked credits (Protect + Compare, as charged when first run): 575

## Not flagged by Compare

- P001: ['atorvastatin']
- P002: ['omeprazole']
- P003: ['warfarin']
- P005: ['salbutamol inhaler']
- P006: ['amlodipine']
- P008: ['amlodipine']
- P009: ['insulin glargine', 'levothyroxine']
- P010: ['levothyroxine']
- P012: ['lisinopril']
- P015: ['lisinopril']
- P017: ['insulin glargine']
- P018: ['warfarin']
- P019: ['omeprazole']

## Compare only

