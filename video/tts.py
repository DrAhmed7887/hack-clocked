"""Narration: one ElevenLabs request per shot, with character timestamps, so cuts and highlights follow the voice.

Output: runs/video/audio/S1.mp3 and S1.json (cue times in seconds). Key from Keychain ELEVENLABS_API_KEY.
"""
import base64
import json
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "runs" / "video" / "audio"


def key() -> str:
    return subprocess.run(["security", "find-generic-password", "-s", "ELEVENLABS_API_KEY", "-w"],
                          capture_output=True, text=True, check=True).stdout.strip()


def cue_times(text: str, starts: list, cues: list) -> dict:
    out = {}
    for word, beat in cues:
        i = text.find(word)
        if i < 0:
            raise ValueError(f"cue word {word!r} not in line")
        out[beat] = round(starts[i], 3)
    return out


def main() -> None:
    cfg = json.loads((ROOT / "video" / "narration.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    k = key()
    for shot in cfg["shots"]:
        mp3, meta = OUT / f"{shot['id']}.mp3", OUT / f"{shot['id']}.json"
        if mp3.exists() and meta.exists() and json.loads(meta.read_text()).get("text") == shot["text"] \
                and json.loads(meta.read_text()).get("speed") == 1.0:
            continue  # unchanged line: keep the existing take, spend nothing
        body = json.dumps({"text": shot["text"], "model_id": cfg["model_id"],
                           "voice_settings": {"stability": 0.6, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0}}).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}/with-timestamps?output_format=mp3_44100_128",
            data=body, headers={"xi-api-key": k, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read())
        mp3.write_bytes(base64.b64decode(d["audio_base64"]))
        al = d["alignment"]
        meta.write_text(json.dumps({"text": shot["text"], "speed": 1.0, "duration": al["character_end_times_seconds"][-1],
                                    "chars": al["characters"], "starts": al["character_start_times_seconds"],
                                    "ends": al["character_end_times_seconds"],
                                    "cues": cue_times(shot["text"], al["character_start_times_seconds"], shot["cues"])},
                                   indent=1))
        print(shot["id"], "ok", round(al["character_end_times_seconds"][-1], 2), "s")


if __name__ == "__main__":
    main()
