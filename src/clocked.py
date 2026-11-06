"""Minimal Clocked API client: POST JSON with Bearer key from Keychain, idempotent retries, on-disk cache."""
import hashlib
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "https://clocked.rezolve.ai/clocked"
CACHE = Path(__file__).resolve().parent.parent / "runs" / "raw"


def _key() -> str:
    key = os.environ.get("CLOCKED_API_KEY") or subprocess.run(
        ["security", "find-generic-password", "-s", "CLOCKED_API_KEY", "-w"],
        capture_output=True, text=True).stdout.strip()
    if not key:
        raise RuntimeError("CLOCKED_API_KEY not set (env or Keychain)")
    return key


def call(endpoint: str, payload: dict, retries: int = 3) -> dict:
    """POST to a Clocked endpoint. Identical payloads are served from the cache (no credits spent twice)."""
    body = json.dumps(payload, sort_keys=True).encode()
    digest = hashlib.sha256(endpoint.encode() + body).hexdigest()[:24]
    cached = CACHE / f"{endpoint}_{digest}.json"
    if cached.exists():
        return json.loads(cached.read_text())
    idem = str(uuid.uuid4())  # reused across retries so a retry is never charged twice
    for attempt in range(retries + 1):
        req = urllib.request.Request(f"{BASE}/{endpoint}", data=body, method="POST", headers={
            "Authorization": f"Bearer {_key()}", "Content-Type": "application/json", "Idempotency-Key": idem})
        try:
            with urllib.request.urlopen(req, timeout=130) as resp:
                data = json.loads(resp.read())
                data["_credits"] = resp.headers.get("X-Clocked-Credits")
                CACHE.mkdir(parents=True, exist_ok=True)
                cached.write_text(json.dumps(data, indent=1))
                return data
        except urllib.error.HTTPError as err:
            if err.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(float(err.headers.get("Retry-After") or 2 ** attempt))
                continue
            detail = err.read().decode(errors="replace")[:300]  # error body never contains the key
            raise RuntimeError(f"{endpoint} HTTP {err.code}: {detail}") from None
    raise RuntimeError(f"{endpoint}: retries exhausted")
