# Review: Clocked teaser v1 (30 s, 1080x1080)

Made 8 Nov 2026 as a test of the teaser template against the 2:32 film (`../film`).

## What it is
Opener (3.0 s) → 5 scenes of real site footage or real numbers (23.8 s) → end card (3.2 s). One caption per scene
(label, title of 5 words or fewer, one subtitle). Fixed frame: corners, brand, scene counter, progress line.
Music: last 30 s of the film's own track (`music.mp3`, from 120 s); a tick on each real click, a soft pop on each caption.

## Measured
- `hyperframes check`: 0 errors. Kept warning: `timeline_track_too_dense` (the 5 scene counters in `frame.html`).
- All reading text 28 px or more (labels 28, subtitles 30, titles 56). Site text shows at about 27 px.
- Loudness −16.8 LUFS integrated, peak −1.5 dBFS (measured with ffmpeg ebur128, not heard).
- Watched as frames at 1 fps across all 30 s and at 10 fps across one transition.

## Fixed during review
- The opener clip began on the home page's embedded film player; it now starts on the patient table.
- Scenes 2 and 4 re-showed the top of the page before scrolling; each clip now starts near its target.
- The opener was nearly empty for the first second (bad for muted autoplay); text now lands from 0.2 s.
- The cursor covered the removed sentence; it now moves aside after the click.
- Music was −19.3 LUFS; raised to −16.8.

## Not checked
- Sound by ear. Every transition at full speed by a person (G4: Ahmed watches with sound).

## Weakest shot
- Scene 3 starts on the allergy banner that scene 2 just showed (continuity, but a repeat). With more time: start it on "Written handoff".
