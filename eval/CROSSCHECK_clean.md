# Cross-check results, clean set (20 packets)

Produced by `python3 eval/score_crosscheck.py`. Synthetic data only.

- Privacy gate (Clocked Protect) passed: **20/20** packets
- Rule-found dose/stop/allergy conflicts also flagged by Clocked Compare: **24/39**
- Compare conflicts that no rule explained (shown to the clinician for review): **0**
- Clocked credits (Protect + Compare, as charged when first run): 555

## Not flagged by Compare

- P002: ['omeprazole']
- P003: ['warfarin']
- P005: ['salbutamol inhaler']
- P006: ['amlodipine']
- P008: ['amlodipine']
- P009: ['insulin glargine', 'levothyroxine']
- P010: ['levothyroxine']
- P012: ['lisinopril']
- P013: ['allergy', 'atorvastatin']
- P015: ['lisinopril']
- P017: ['insulin glargine']
- P018: ['warfarin']
- P019: ['omeprazole']

## Compare only

