"""Narration: one ElevenLabs request per scene with character timestamps, then the scene clock (timings.json).

Key from Keychain ELEVENLABS_API_KEY. Unchanged lines are not re-requested. Output: assets/audio/voice/<id>.mp3,
timings.json = {total, scenes: [{id, start, dur, voice_at, voice_len, cues: {name: absolute seconds}, words: [...]}]}.
"""
import base64
import json
import pathlib
import re
import subprocess
import urllib.request

HERE = pathlib.Path(__file__).parent
OUT = HERE / "assets" / "audio" / "voice"
LEAD, GAP = 0.35, 0.6  # silence before each line, default silence after it


def key() -> str:
    return subprocess.run(["security", "find-generic-password", "-s", "ELEVENLABS_API_KEY", "-w"],
                          capture_output=True, text=True, check=True).stdout.strip()


def tts(cfg: dict, scene: dict, k: str) -> dict:
    mp3, meta = OUT / f"{scene['id']}.mp3", OUT / f"{scene['id']}.json"
    if mp3.exists() and meta.exists() and json.loads(meta.read_text())["text"] == scene["text"]:
        return json.loads(meta.read_text())
    body = json.dumps({"text": scene["text"], "model_id": cfg["model_id"],
                       "voice_settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0}}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": k, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    mp3.write_bytes(base64.b64decode(d["audio_base64"]))
    al = d["alignment"]
    m = {"text": scene["text"], "starts": al["character_start_times_seconds"], "ends": al["character_end_times_seconds"]}
    meta.write_text(json.dumps(m))
    print(scene["id"], "voiced", round(m["ends"][-1], 2), "s")
    return m


def words(text: str, starts: list, ends: list) -> list:
    return [{"text": w.group(), "start": round(starts[w.start()], 3), "end": round(ends[w.end() - 1], 3)}
            for w in re.finditer(r"\S+", text)]


def main() -> None:
    cfg = json.loads((HERE / "script.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    k, t, scenes = key(), 0.0, []
    for sc in cfg["scenes"]:
        m = tts(cfg, sc, k)
        voice_len = m["ends"][-1]
        cues = {}
        for word, name in sc["cues"]:
            i = sc["text"].find(word)
            if i < 0:
                raise ValueError(f"{sc['id']}: cue {word!r} not in line")
            cues[name] = round(t + LEAD + m["starts"][i], 3)
        dur = round(LEAD + voice_len + sc.get("tail", GAP), 3)
        scenes.append({"id": sc["id"], "start": round(t, 3), "dur": dur, "voice_at": round(t + LEAD, 3),
                       "voice_len": round(voice_len, 3), "cues": cues,
                       "words": [{**w, "start": round(w["start"] + t + LEAD, 3), "end": round(w["end"] + t + LEAD, 3)}
                                 for w in words(sc["text"], m["starts"], m["ends"])]})
        t += dur
    (HERE / "timings.json").write_text(json.dumps({"total": round(t, 3), "scenes": scenes}, indent=1))
    for s in scenes:
        print(f"{s['id']:8} {s['start']:7.2f} +{s['dur']:5.2f}  cues {s['cues']}")
    print("total", round(t, 2))


if __name__ == "__main__":
    main()
