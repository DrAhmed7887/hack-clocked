# Review: Clocked film v2 (storyline A, "One sentence on trial")

## Creative calls
- One patient (synthetic P001) carries the film; one allergy sentence is the spine: Fill drafts it, Verify marks it
  contradicted (score 0.40, from the recorded Verify response), the rules rebuild it from two exact quotes, and Verify
  supports each quote alone. P019 appears once, labelled, for the absence case.
- The app's own light page and colours; each colour means one thing (red conflict, green verified, amber medication
  flag, blue "by comparing records"). Real site captures for every finished output (removed fold-out, final sentence,
  banner, cross-checks, P019 handoff); rebuilt elements show only real strings copied from the pipeline output.
- An endpoint rail (Protect, Extract, Rules, Fill, Verify, Compare) names what is working in each scene.
- Not built: storylines B (four records become one) and C (the deleted sentence as a case file); see STORYLINES.md in Drive.
- Video-director review (7 Nov) applied: handoff defined in the hook, records merged into the hook, Verify line says the
  contradicted verdict is correct, rebuild credits Clocked Verify, Compare adds "none the rules had missed",
  54/100 moved to the numbers, 55/70 shown at full size.

## Measured, looked at, not checked
- `hyperframes check`: 0 errors. Warnings kept: text_below_floor (record card text is 16.5 px at full view; it is read at
  1.7x in the hook, and every line that matters is restated at 28 px or more), line_unread on a card label during a move,
  and the Fill sentence (it stays on screen through the Verify scene, about 18 s in total).
- Looked at: 24 frames across the film (snapshots). Not looked at: every transition at full speed.
- Sound was measured, not heard: voice at -16 LUFS per line, music bed at 0.14 under the voice, dipped to 0.04 at the deletion.

## Weakest shot
- Protect and Extract: the record cards are small at full view; the boxes carry the scene, not the text.
  With more time: push in on one card during each.
