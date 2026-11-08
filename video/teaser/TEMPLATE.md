# Teaser template (30 s square, real app footage)

Three files make the whole video:

1. `record.mjs`: walks the live app with Playwright, one screenshot per frame (sharp 1920x1200, scripted cursor and
   clicks, identical every run). Edit the `CLIPS` functions for a new app. Run `node record.mjs`.
2. `teaser.json`: all words, timings and clips (intro, 5 scenes, numbers, end card, music, sounds).
3. `build.mjs`: turns the JSON into the HyperFrames project (look and motion live here). Run `node build.mjs`.

Then: `npx hyperframes check`, `npx hyperframes snapshot --at ...`, `npx hyperframes render`.

Rules that make it work: one idea per scene; titles of 5 words or fewer; no reading text under 28 px; real screens,
never rebuilt ones; each clip starts near its target (no repeated screens); the first second already shows the title;
loudness about −16 LUFS; watch it at full speed with sound before calling it done.

Needs: Node, `npm install` (Playwright 1.64.1, uses the browsers already in ~/Library/Caches/ms-playwright), ffmpeg.
