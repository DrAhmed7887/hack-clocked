# G1 results (20 synthetic packets, 61 documents)

Produced by `python3 eval/score.py`. Synthetic data only.

- Allergy state correct: **20/20**
- Allergy conflicts flagged: **5/5**
- Medication labels correct: **100/100**
- Medication discrepancies flagged (any non-consistent label): **65/65**
- Invented medications: **0**; invented problems: **0**; missed problems: **0**
- Clocked credits used (this run, excluding cached calls): 476

| Medication label | correct |
|---|---|
| consistent | 35/35 |
| dose_differs | 16/16 |
| new_start | 14/14 |
| possible_omission | 17/17 |
| stopped | 18/18 |

Allergy (truth → got): conflicting→conflicting: 5, known→known: 5, nkda→nkda: 5, no_info→no_info: 5

## Medication errors


## Invented / missed

