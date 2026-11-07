"""Assemble the demo film: timed stills/moves + narration + burned-in captions (from the script, never ASR).

Inputs: runs/video/timeline.json (capture.mjs), runs/video/audio/S*.mp3/.json (tts.py).
Output: runs/video/clocked_demo.mp4 (1920x1080, 30 fps, -16 LUFS), contact sheet, QA report.
"""
import json
import re
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
V = ROOT / "runs" / "video"
FONT = "/System/Library/Fonts/Helvetica.ttc"
W, H = 1920, 1080


def run(args):
    subprocess.run(args, check=True)


def caption_chunks(meta: dict, offset: float) -> list:
    """Split a narration line into caption chunks of at most 2 lines x 42 characters, timed by character."""
    text, starts, ends = meta["text"], meta["starts"], meta["ends"]
    pieces, i = [], 0
    for m in re.finditer(r"[^.:;,]+[.:;,]?\s*", text):
        pieces.append((m.start(), m.end()))
    chunks, cur = [], None
    for a, b in pieces:
        if cur and (b - cur[0]) <= 84:
            cur = (cur[0], b)
        else:
            if cur:
                chunks.append(cur)
            cur = (a, b)
    if cur:
        chunks.append(cur)
    out = []
    for a, b in chunks:
        seg = text[a:b].strip()
        b_last = a + len(text[a:b].rstrip()) - 1
        out.append({"text": "\n".join(textwrap.wrap(seg, 42)[:2]),
                    "start": offset + starts[a], "end": offset + ends[min(b_last, len(ends) - 1)]})
    for x, y in zip(out, out[1:]):  # no flicker between chunks
        if y["start"] - x["end"] < 0.35:
            x["end"] = y["start"]
    return out


def caption_png(text: str, path: Path) -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 40)
    lines = text.split("\n")
    widths = [d.textlength(l, font=font) for l in lines]
    lh, pad = 52, 18
    box_w, box_h = max(widths) + 2 * pad, lh * len(lines) + 2 * pad - 8
    x0, y0 = (W - box_w) / 2, H - 40 - box_h
    d.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=10, fill=(29, 29, 27, 220))
    for k, l in enumerate(lines):
        d.text(((W - widths[k]) / 2, y0 + pad + k * lh - 4), l, font=font, fill=(255, 255, 255, 255))
    img.save(path)


def main() -> None:
    tl = json.loads((V / "timeline.json").read_text())
    lead = tl["lead"]
    # 1. picture: one still per output frame at a fixed 30 fps, picked by absolute time, so it never drifts
    #    from the voice (a concat list rounds sub-frame segments up and drifted 1.6 s over the film).
    seq = V / "seq"
    if seq.exists():
        for f in seq.iterdir():
            f.unlink()
    seq.mkdir(exist_ok=True)
    events = sorted((shot["start"] + s["t"], s["file"]) for shot in tl["shots"] for s in shot["segs"])
    n_frames, j = round(tl["total"] * 30), 0
    for n in range(n_frames):
        while j + 1 < len(events) and events[j + 1][0] <= n / 30 + 1e-6:
            j += 1
        (seq / f"{n:06d}.png").symlink_to(events[j][1])
    run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "30", "-i", str(seq / "%06d.png"),
         "-vf", f"scale={W}:{H},format=yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         str(V / "picture.mp4")])
    # 2. sound: each shot's voice at its absolute offset, then loudness-normalised
    inputs, filt, mix = [], [], []
    for i, shot in enumerate(tl["shots"]):
        inputs += ["-i", str(V / "audio" / f"{shot['id']}.mp3")]
        ms = int((shot["start"] + lead) * 1000)
        filt.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
        mix.append(f"[a{i}]")
    filt.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0,apad,atrim=0:{tl['total']:.3f},"
                "loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[aout]",
         "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(V / "sound.m4a")])
    # 3. captions as transparent overlays
    capdir = V / "captions"
    capdir.mkdir(exist_ok=True)
    caps = []
    for shot in tl["shots"]:
        meta = json.loads((V / "audio" / f"{shot['id']}.json").read_text())
        caps += caption_chunks(meta, shot["start"] + lead)
    args = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(V / "picture.mp4"), "-i", str(V / "sound.m4a")]
    chain, last = [], "0:v"
    for k, c in enumerate(caps):
        png = capdir / f"c{k:03d}.png"
        caption_png(c["text"], png)
        args += ["-i", str(png)]
        chain.append(f"[{last}][{k + 2}:v]overlay=0:0:enable='between(t,{c['start']:.3f},{c['end']:.3f})'[v{k}]")
        last = f"v{k}"
    args += ["-filter_complex", ";".join(chain), "-map", f"[{last}]", "-map", "1:a", "-c:v", "libx264", "-crf", "18",
             "-preset", "medium", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(V / "clocked_demo.mp4")]
    run(args)
    (V / "captions.json").write_text(json.dumps(caps, indent=1, ensure_ascii=False))
    # 4. QA: contact sheet (one frame every 6 s), silence check, loudness
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(V / "clocked_demo.mp4"), "-vf",
         "fps=1/6,scale=480:270,tile=4x6", "-frames:v", "1", str(V / "contact_sheet.png")])
    sil = subprocess.run(["ffmpeg", "-i", str(V / "clocked_demo.mp4"), "-af", "silencedetect=n=-45dB:d=4", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    loud = subprocess.run(["ffmpeg", "-i", str(V / "clocked_demo.mp4"), "-af", "ebur128=peak=true", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    integrated = re.findall(r"I:\s+(-?[\d.]+) LUFS", loud)
    report = {"duration_s": round(tl["total"], 2), "captions": len(caps),
              "silences_over_4s": re.findall(r"silence_duration: ([\d.]+)", sil),
              "integrated_lufs": integrated[-1] if integrated else None}
    (V / "qa.json").write_text(json.dumps(report, indent=1))
    print(report)


if __name__ == "__main__":
    main()
