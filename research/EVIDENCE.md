# Evidence-Linked Clinical Handoff: research pack

Checked 7 Nov 2026 by Claude through PubMed (NCBI) and the HL7 IPS guide. Every public number must come from a row here.
Status: **clinical rules R1–R9 signed off by Ahmed, 7 Nov 2026.**

## A. Evidence

| # | Claim | Source | Exact number / quote | Checked |
|---|---|---|---|---|
| E1 | Medication history errors at admission are common | Tam VC et al., CMAJ 2005;173(5):510-5, systematic review, 22 studies, 3,755 patients. PMID 16129874, [doi:10.1503/cmaj.045311](https://doi.org/10.1503/cmaj.045311) | "Errors in prescription medication histories occurred in up to 67% of cases"; omission 10%–61%, commission 13%–22%; "11%-59% of the medication history errors were clinically important" | 7 Nov 2026 |
| E2 | Discrepancy types: omission and commission | same as E1 | omission = "deletion of a drug used before admission"; commission = "addition of a drug not used before admission" | 7 Nov 2026 |
| E3 | Standardised handoff reduces errors | Starmer AJ et al., NEJM 2014;371:1803-12 (I-PASS), 10,740 admissions, 9 hospitals. PMID 25372088, [doi:10.1056/NEJMsa1405556](https://doi.org/10.1056/NEJMsa1405556) | medical-error rate fell 23% (24.5 → 18.8 per 100 admissions); preventable adverse events fell 30% (4.7 → 3.3 per 100) | 7 Nov 2026 |
| E4 | Medication and allergy lists disagree with what patients report | Andrus MR, Anderson AD, Pharm Pract 2015;13(1):518, 557 outpatient reconciliations. PMID 25883689, [doi:10.18549/pharmpract.2015.01.518](https://doi.org/10.18549/pharmpract.2015.01.518) | 3.2 medication discrepancies per patient; 272 allergy discrepancies; commonest: medications no longer taken (37.3%) | 7 Nov 2026 |
| E5 | AI summaries of outside-facility records miss and misstate facts | Park KU et al., Ann Surg Oncol 2026;33(10):9102-9, 62 cases, GPT-4o + RAG. PMID 42455485, [doi:10.1245/s10434-026-20170-w](https://doi.org/10.1245/s10434-026-20170-w) | "Thoroughness without omission was rated low in 28 (45%) summaries"; errors in 25 (40%), "13 (52%) classified as critical (treatment-impacting)" | 7 Nov 2026 |
| E6 | LLM transfer-call summaries: thoroughness and hallucination are the weakest domains | Wrenn JO et al., J Med Internet Res 2026;28:e88834, 31 STEMI transfer calls. PMID 42348906, [doi:10.2196/88834](https://doi.org/10.2196/88834) | "thorough" 4.4/5 and "hallucination free" 4.4/5 were the lowest-rated domains | 7 Nov 2026 |
| E7 | A patient summary must contain problems, allergies and medications | HL7 International Patient Summary IG v2.0.0 (STU 2), "Structure of the IPS", https://hl7.org/fhir/uv/ips/STU2/ | Required (R): "Problem List, Allergies and Intolerances, and Medication Summary"; recommended: immunizations, diagnostic results, procedures, devices | 7 Nov 2026 |
| E8 | IPS does not distinguish "no known allergies" from "no information" by separate coding | same as E7 | "If no information about allergies is available, or if no allergies are known, this should be documented … through the use of emptyReason" | 7 Nov 2026 |

Not used (unverified, keep out of public material): a "best possible medication history needs ≥2 sources" rule (WHO High 5s / ISMP Canada) has not been read from the source yet.

## B. Clinical rules for the app (Ahmed signs these)

| Rule | What the app does | Based on | Ahmed's sign-off |
|---|---|---|---|
| R1 | The handoff always has three sections: Problems, Allergies & intolerances, Medications. Immunizations shown when present. | E7 | ✅ 7 Nov 2026 |
| R2 | Every fact carries one status: **Supported** (stated in at least one source, contradicted by none), **Conflicting** (sources disagree), or **Not found** (no source mentions it). Each fact cites the document and the exact text it came from. | E5, E6; design | ✅ 7 Nov 2026 |
| R3 | "No known allergies" (a source says so) and "No allergy information found" (no source mentions allergies) are shown as two different states. Absence is never turned into "no allergies". | E8 (IPS merges them; the app keeps them apart on purpose) | ✅ 7 Nov 2026 |
| R4 | Medication differences between sources are labelled: present in an older source but missing from the newest (possible **omission**), new in the newest source (possible **commission/new start**), **dose or frequency differs**, or **stopped** (a source records the stop). | E1, E2, E4 | ✅ 7 Nov 2026 |
| R5 | Conflicts are never resolved automatically. The newest document is not assumed correct; both versions are shown with their dates and sources, and the clinician decides. | E5 (critical errors); design | ✅ 7 Nov 2026 |
| R6 | Any allergy conflict appears at the top of the handoff, highlighted, before anything else. | E4; clinical judgement | ✅ 7 Nov 2026 |
| R7 | Every sentence in the generated handoff is checked against the sources (Clocked Verify/grounding). An unsupported sentence is removed and listed as "removed: not supported by any source". | E5, E6 | ✅ 7 Nov 2026 |
| R7a | Exception to R7 for absences: a text checker cannot prove that something is missing. A sentence saying a medicine is absent from the newest record (R4 "possible omission"), or that no record mentions allergies (R3), is kept and marked "established by record comparison", not removed. | Found 7 Nov: Clocked Verify removed the correct "warfarin is missing from the newest record" sentence as not_stated. | ☐ |
| R7b | Safety net: any discrepancy the generated text does not name is added from the rules as a sentence built only from verbatim quotes, marked "added by rules", with Clocked Verify's verdict shown beside it. The written handoff can never name fewer discrepancies than the structured view. | Found 7 Nov: generated text named 60/70 discrepancies before this rule, 70/70 after. | ☐ |
| R8 | The app is decision support for a clinician, not a diagnosis or a prescription. It never suggests which medication or dose is right. | design; safety | ✅ 7 Nov 2026 |
| R9 | Prescriber shorthand and Spanish terms are mapped to one meaning before comparing: BD / b.i.d. / cada 12 horas = twice daily; OD / o.d. / daily / una vez al día = once daily; nocte / ON / por la noche = at night; PRN / when required / a demanda = as needed; mane before food / en ayunas = morning, fasting; mcg = micrograms = microgramos. Spanish drug and problem names map to the English generic (fixed list in `src/normalize.py`). A term not on the list is shown as written, never guessed. | Standard prescribing abbreviations; Ahmed's clinical judgement. Added 7 Nov after G1 (realistic wording broke matching: 54/100 → 100/100 after this rule). | ✅ 7 Nov 2026 |

## C. Test-set measures (Gate G1)
- **Conflict recall:** of the planted conflicts in each synthetic packet, how many the handoff flags (target: all allergy conflicts).
- **Fabrication rate:** facts in the handoff that no source supports (target: 0 after R7).
- **Omission rate:** planted facts missing from the handoff.
- Each measured on a fixed, seeded set of synthetic packets; numbers come from a script only.
