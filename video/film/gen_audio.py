"""Music bed and sound effects for the film (ElevenLabs; key from Keychain ELEVENLABS_API_KEY, never printed).

Existing files are kept; pass --force to remake them. Output: assets/audio/raw/*.mp3
"""
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent
RAW = HERE / "assets" / "audio" / "raw"
API = "https://api.elevenlabs.io/v1"
SFX = {
    "tick_a": ("Very soft short keyboard key tick, single, clean, close", 0.5),
    "tick_b": ("Soft single mechanical key tap, quiet and crisp", 0.5),
    "stamp": ("Single firm rubber stamp pressed onto paper on a desk, short thud", 0.6),
    "pop": ("Small soft UI pop of a label appearing, gentle, no musical tone", 0.5),
    "whoosh_a": ("Quick soft air whoosh of a paper sheet sliding across a desk", 0.7),
    "whoosh_b": ("Short gentle swish of a card flying past, light", 0.6),
    "scan": ("Soft smooth scanner light sweep across paper, quiet electronic hum, short", 1.2),
}
MUSIC_PROMPT = (
    "Calm, focused, minimal underscore for a clinical software demo film. Soft felt piano, warm low synth pulse, light "
    "brushed percussion, 88 bpm, steady and serious, sits under narration, no vocals, no big drops. Middle section "
    "thins out to sparse piano and pulse; final section warmer and brighter with a resolved last bar."
)
MUSIC_MS = 150000


def key() -> str:
    return subprocess.run(["security", "find-generic-password", "-s", "ELEVENLABS_API_KEY", "-w"],
                          capture_output=True, text=True, check=True).stdout.strip()


def post(k: str, path: str, body: dict, dest: pathlib.Path) -> bool:
    req = urllib.request.Request(f"{API}{path}", data=json.dumps(body).encode(),
                                 headers={"xi-api-key": k, "Content-Type": "application/json"})
    try:
        dest.write_bytes(urllib.request.urlopen(req, timeout=400).read())
        return True
    except urllib.error.HTTPError as e:
        print(f"failed {dest.name}: HTTP {e.code} {e.read()[:200]!r}", file=sys.stderr)
        return False


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    k, force = key(), "--force" in sys.argv
    for name, (prompt, secs) in SFX.items():
        dest = RAW / f"sfx_{name}.mp3"
        if force or not dest.exists():
            print(name, post(k, "/sound-generation", {"text": prompt, "duration_seconds": secs, "prompt_influence": 0.6}, dest))
    dest = RAW / "music.mp3"
    if force or not dest.exists():
        print("music", post(k, "/music", {"prompt": MUSIC_PROMPT, "music_length_ms": MUSIC_MS}, dest))


if __name__ == "__main__":
    main()
