# Data card: synthetic record packets

**Synthetic only. No real patients, no real names, no real records.** Patients are labelled `synthetic case P001`–`P020`.

## What it is
20 packets (`data/packets/packet_XX.json`), each 2–4 plain-text documents about one synthetic patient, written in different settings and on different dates:
- discharge summary (internal medicine ward, Cairo, "translated to English"), outpatient clinic note (Alexandria), GP referral letter (Valencia), community pharmacy dispensing record (Valencia; lists medicines only, no diagnoses).

Each packet has an answer key (`truth`) used only for scoring, never sent to any API.

## Fields
- `documents[]`: `doc_id`, `kind`, `date` (ISO), `text`.
- `truth.problems[]`: `name`, `status` (`supported` or `not_found`), `sources`. Each packet has one decoy problem that no document mentions.
- `truth.allergy`: `state` = `known` (same allergy in every document), `conflicting` (one document records an allergy, another says "No known drug allergies"), `nkda` (only "No known drug allergies" statements), `no_info` (no document mentions allergies). Each state occurs in 5 of 20 packets. Rule R3: `nkda` and `no_info` must be shown differently.
- `truth.medications[]`: `drug`, `label`, `status`, `per_doc`. Labels (rule R4): `consistent`, `dose_differs` (newest document has a different dose), `possible_omission` (in older documents, absent from the newest, no stop recorded), `new_start` (only in the newest), `stopped` (newest document records the stop).

## Where the design comes from
- Discrepancy types: omission and commission, Tam et al. 2005 (EVIDENCE.md E1–E2).
- "No longer taking" as the commonest discrepancy: Andrus & Anderson 2015 (E4), represented by `stopped` and `possible_omission`.
- Required sections (problems, allergies, medications): HL7 IPS STU2 (E7).
- Allergy "no information" vs "no known allergies": IPS treats both with `emptyReason` (E8); the app keeps them apart (R3).

## Known limits
- Drug and problem lists are drawn at random: a packet can list warfarin without atrial fibrillation. The packets test **record comparison**, not prescribing logic.
- Frequencies of each label are fixed by design, not taken from real prevalence. No number from this data describes real patients.
- English only (the Cairo document is presented as already translated).

## Reproduce
`python3 data/generate.py` (seed `20261107`) regenerates the identical files.
