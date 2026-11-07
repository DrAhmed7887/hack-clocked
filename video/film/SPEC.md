# Clocked demo film v2: "One sentence on trial" (storyline A)

GOAL:    A judge finishes knowing that every sentence in this handoff was either verified against the source
         records by Clocked or labelled for what it is, and that the tool deleted a sentence it could not support
         and rebuilt it from exact quotes. Five Clocked endpoints each visibly did one job.
OUTPUT:  HyperFrames 0.9.11 (plugin), 1920 x 1080, 30 fps.
TIME:    about 140 s x 30 = about 4200 frames. The voice is the clock (one ElevenLabs line per scene, character
         timestamps). Music bed at 0.14 under the voice.
LOOK:    The app's own page, enlarged: this is product UI, not a poster.
         - Ground: #F6F5F1 flat (the app's --bg), no texture, no gradient.
         - Paper: record and handoff cards are #FFFFFF, 1 px #E2E0D8 border, radius 14 px,
           shadow 0 18px 40px rgba(29,29,27,0.08).
         - Ink: #1D1D1B; muted #5D5D58.
         - Meaning colours, each only for its meaning: red #A4161A on #FDE8E8 = conflict or contradicted;
           green #1F7A4D on #E6F3EC = verified/supported; amber #9A5B00 on #FDF0DC = a medication flag;
           blue #2B5C9E on #E7EEF9 = "established by comparing records". No other accent.
         - Type: Inter 400/700/900. Display 64-88 px, -2% tracking. Record text: JetBrains Mono 30-34 px (records
           are monospace on the site). Labels on parts 28 px minimum.
OBJECTS: - Record card: a white sheet with its header line as on the site (e.g. "Pharmacy record, 2025-04-17"),
           the record's real text in mono. Four of them: Clinic note (Alexandria), Discharge summary (Cairo, translated),
           Pharmacy record (Valencia), GP letter (Valencia, Spanish).
         - The handoff sheet: a white card titled "Written handoff", where sentences are typed, judged and replaced.
         - The verdict stamp: a rounded label with the verdict word and score ("contradicted · 0.40").
         - Real site captures (2x) as cut-ins inside the same card style: the removed fold-out, the written
           handoff, the cross-checks panel, P019's absence sentence, the method numbers.
MOTION:  - Arrive: expo.out 0.5 s. Move/camera: power2.inOut 0.7 s. Exit: power3.in 0.3 s.
         - Lines lifting out of a record: 0.45 s power3.out, 80 ms stagger.
         - Stamps: a 0 ms set at the hit, then scale 1.12 -> 1 in 0.18 s power2.out (no bounce on UI).
         - Strike-through: a 4 px red bar drawn left to right 0.35 s power1.inOut.
         - Camera: one wrapper per scene, scale/x/y only.
SHOTS:   (times are targets; the voice sets the real ones)
         1. Hook 0-10: frame 0 = GP letter card, its line "Sin alergias medicamentosas conocidas." boxed, gloss
            "no known drug allergies" beneath. Pharmacy card slides in from the right; "Allergies: sulfonamides (hives)"
            boxed red. Both stay. Sound: low pulse starts.
         2. Records 10-19: camera pulls back; the clinic note and discharge summary join; four cards in a row
            fan, each with its city/date label on it.
         3. Protect 19-28: a scan line passes each card; "synthetic case P001" lights green with "allowed" on each
            card (the four real hits). Sound: one soft tick per card.
         4. Extract 28-37: lines lift out of the cards word for word, each with its [start, end] offsets; the
            allergy lines first, then the medication lines.
         5. Rules 37-48: chips stamp onto the lifted items in the app's words: "Allergy conflict",
            "Missing from newest record" (warfarin: three ticks, "not listed"), "Dose or timing differs" (bisoprolol 2.5 -> 5).
            "Physician-signed rules" label; "No model decides a label".
         6. Fill 48-55: the handoff sheet takes the frame; Fill's allergy sentence types in (real text).
         7. Verify 55-68 (hero): the sentence is checked against the records; stamp "contradicted · 0.40"; red strike;
            the sentence drops into a "Removed by Verify" tray. Cut-in: the real removed fold-out from the site.
         8. Rebuild 68-82: the two exact quotes fly out of the pharmacy and GP cards into the sheet and form the
            final sentence; each quote gets its own green "supported" stamp; badge "Added by rules · Each quote verified".
            Cut-in: the real written handoff card.
         9. Quiet 82-96: four metformin lines (bd / bd / b.i.d. / cada 12 horas) collapse into "500 mg | 2/day",
            chip "Same in all records". Then "54/100 -> 100/100 medication labels" with "before / after normalisation".
         10. Compare 96-104: the real cross-checks panel; count 25 of 39.
         11. Absence 104-116: "Another synthetic patient · P019": the lisinopril sentence with the blue
             "Established by comparing records" label; "No record mentions allergies: allergy status is unknown, not 'no allergies'."
         12. Numbers 116-132: one number per line, each when said: 100/100 labels, 5/5 allergy conflicts,
             70/70 discrepancies (55 with Fill + Verify alone, shown smaller), 0 invented medicines.
         13. End 132-140: "Every sentence verified, or labelled for what it is." Repo URL. "Synthetic records only.
             Decision support, not a prescription." Held 4 s.
BANNED:  The defaults in spec.md, plus:
         - any screen of app output that the app did not produce (all sentences, quotes, scores, chips are copied
           from runs and the site);
         - any wording that recommends a drug, dose or action (rule R8);
         - real names, or any patient detail beyond the synthetic code;
         - a dark ground; glows; the logo docked in a corner;
         - text moving while it is read; every scene entering with a fade-up.
QA:      Frames at 0.2, 5, 9, 15, 24, 33, 42, 52, 60, 64, 72, 80, 88, 94, 100, 110, 120, 128, 136 s, at 1920 and 360 wide.
         Every number on screen checked against eval/*.md.
