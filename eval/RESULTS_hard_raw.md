# G1 results, hard set WITHOUT normalisation (baseline) (20 synthetic packets, 61 documents)

Produced by `python3 eval/score.py`. Synthetic data only.

- Allergy state correct: **20/20**
- Allergy conflicts flagged: **5/5**
- Medication labels correct: **54/100**
- Medication discrepancies flagged (any non-consistent label): **61/65**
- Problems found: **42/57**
- Invented medications: **47**; invented problems: **35**; missed problems: **15**
- Clocked credits charged when these calls were first made: 474

| Medication label | correct |
|---|---|
| consistent | 4/35 |
| dose_differs | 10/16 |
| new_start | 10/14 |
| possible_omission | 17/17 |
| stopped | 13/18 |

Allergy (truth → got): conflicting→conflicting: 5, known→known: 5, nkda→nkda: 5, no_info→no_info: 5

## Medication errors

- P001: atorvastatin truth=stopped got=possible_omission
- P001: metformin truth=consistent got=possible_omission
- P001: omeprazole truth=consistent got=possible_omission
- P002: metformin truth=consistent got=dose_differs
- P002: salbutamol inhaler truth=consistent got=dose_differs
- P003: bisoprolol truth=consistent got=dose_differs
- P003: levothyroxine truth=consistent got=dose_differs
- P004: levothyroxine truth=new_start got=MISSING
- P004: salbutamol inhaler truth=consistent got=possible_omission
- P004: metformin truth=dose_differs got=possible_omission
- P004: atorvastatin truth=consistent got=possible_omission
- P005: atorvastatin truth=consistent got=dose_differs
- P006: omeprazole truth=dose_differs got=possible_omission
- P006: levothyroxine truth=new_start got=MISSING
- P006: amlodipine truth=stopped got=possible_omission
- P006: bisoprolol truth=consistent got=dose_differs
- P007: metformin truth=consistent got=dose_differs
- P007: lisinopril truth=consistent got=dose_differs
- P008: salbutamol inhaler truth=consistent got=dose_differs
- P009: salbutamol inhaler truth=consistent got=dose_differs
- P010: salbutamol inhaler truth=consistent got=possible_omission
- P010: levothyroxine truth=dose_differs got=possible_omission
- P010: bisoprolol truth=consistent got=dose_differs
- P011: levothyroxine truth=consistent got=dose_differs
- P012: salbutamol inhaler truth=consistent got=dose_differs
- P013: bisoprolol truth=consistent got=dose_differs
- P013: lisinopril truth=consistent got=dose_differs
- P014: amlodipine truth=consistent got=dose_differs
- P015: bisoprolol truth=consistent got=dose_differs
- P015: warfarin truth=consistent got=dose_differs
- P016: levothyroxine truth=consistent got=dose_differs
- P016: insulin glargine truth=consistent got=dose_differs
- P017: amlodipine truth=dose_differs got=possible_omission
- P017: levothyroxine truth=consistent got=possible_omission
- P017: insulin glargine truth=stopped got=possible_omission
- P017: salbutamol inhaler truth=consistent got=possible_omission
- P018: amlodipine truth=stopped got=possible_omission
- P018: atorvastatin truth=new_start got=MISSING
- P018: warfarin truth=dose_differs got=possible_omission
- P018: bisoprolol truth=consistent got=dose_differs

## Invented / missed

- P001: invented meds ['atorvastatina', 'metformina', 'omeprazol'], invented problems ['enfermedad renal crónica estadio 3a'], missed problems []
- P002: invented meds ['metformina', 'levotiroxina', 'omeprazol', 'atorvastatina', 'salbutamol'], invented problems ['enfermedad renal crónica estadio 3a', 'hiperlipidemia', 'hipertensión arterial esencial'], missed problems []
- P003: invented meds ['omeprazol', 'warfarina', 'levotiroxina'], invented problems ['enfermedad por reflujo gastroesofágico', 'enfermedad renal crónica estadio 3a', 'hipotiroidismo'], missed problems ['atrial fibrillation']
- P004: invented meds ['levotiroxina', 'salbutamol', 'metformina', 'atorvastatina'], invented problems ['diabetes mellitus tipo 2', 'fibrilación auricular', 'hiperlipidemia'], missed problems ['atrial fibrillation', 'hyperlipidaemia', 'type 2 diabetes']
- P005: invented meds ['salbutamol', 'amlodipino', 'atorvastatina'], invented problems ['diabetes mellitus tipo 2', 'enfermedad por reflujo gastroesofágico'], missed problems []
- P006: invented meds ['omeprazol', 'levotiroxina', 'amlodipino'], invented problems ['fibrilación auricular', 'hipertensión arterial esencial'], missed problems []
- P007: invented meds ['metformina', 'amlodipino', 'insulina glargina'], invented problems ['asma', 'diabetes mellitus tipo 2'], missed problems []
- P008: invented meds ['amlodipino', 'insulina glargina', 'salbutamol'], invented problems ['diabetes mellitus tipo 2', 'fibrilación auricular', 'hiperlipidemia'], missed problems []
- P010: invented meds ['salbutamol', 'levotiroxina'], invented problems ['hipertensión arterial esencial', 'hipotiroidismo'], missed problems []
- P011: invented meds ['insulina glargina', 'atorvastatina', 'levotiroxina'], invented problems ['enfermedad por reflujo gastroesofágico', 'fibrilación auricular'], missed problems ['atrial fibrillation']
- P013: invented meds ['atorvastatina', 'amlodipino'], invented problems ['fibrilación auricular', 'hipertensión arterial esencial'], missed problems ['asthma', 'atrial fibrillation']
- P016: invented meds [], invented problems [], missed problems ['gastro-oesophageal reflux disease']
- P017: invented meds ['amlodipino', 'levotiroxina', 'insulina glargina', 'salbutamol'], invented problems ['asma'], missed problems ['asthma']
- P018: invented meds ['amlodipino', 'atorvastatina', 'warfarina'], invented problems ['diabetes mellitus tipo 2', 'enfermedad por reflujo gastroesofágico', 'fibrilación auricular', 'hiperlipidemia'], missed problems ['atrial fibrillation', 'gastro-oesophageal reflux disease', 'hyperlipidaemia', 'type 2 diabetes']
- P019: invented meds ['omeprazol', 'warfarina', 'atorvastatina'], invented problems ['enfermedad renal crónica estadio 3a', 'hiperlipidemia', 'hipotiroidismo'], missed problems ['hypothyroidism']
- P020: invented meds ['levotiroxina', 'amlodipino', 'warfarina'], invented problems ['enfermedad renal crónica estadio 3a', 'fibrilación auricular'], missed problems ['hyperlipidaemia']
