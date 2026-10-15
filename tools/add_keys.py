"""Add extra Gemini API keys to .env without echoing them.

    python tools/add_keys.py          # prompts (hidden input) for up to 3 more keys
    python tools/add_keys.py --parse  # set the dedicated resume-parsing key (GEMINI_PARSE_API_KEY)
    python tools/add_keys.py --list   # show how many keys are configured (never the values)

Keys are typed at a hidden prompt (getpass): not shown, not in shell history, not visible to anyone else.
They are written only to .env (chmod 600, gitignored) as GEMINI_API_KEY_2, _3, ...
Each key is checked with a models.list call (does not use generation quota).
"""
from __future__ import annotations

import getpass
import os
import re
import stat
import sys
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / ".env"
PAT = re.compile(r"^GEMINI_API_KEY(_\d+)?=(.*)$")
PARSE = "GEMINI_PARSE_API_KEY"


def read_env() -> list[str]:
    return ENV.read_text().splitlines() if ENV.exists() else []


def existing(lines: list[str]) -> dict[str, str]:
    return {m.group(0).split("=")[0]: m.group(2) for ln in lines if (m := PAT.match(ln.strip()))}


def check(key: str) -> bool:
    try:
        from google import genai

        client = genai.Client(api_key=key)  # keep a reference: a temporary client is GC-closed mid-request
        next(iter(client.models.list()))
        return True
    except Exception as e:
        msg = str(e).replace(key, "***")[:200]
        print(f"  ✗ key rejected: {type(e).__name__}: {msg}")
        return False


def parse_model() -> str:
    for ln in read_env():
        if ln.startswith("GEMINI_MODEL="):
            return ln.split("=", 1)[1].strip()
    return "gemini-3.1-flash-lite"


def check_generation(key: str, model: str) -> bool:
    """One tiny request: proves the key's project can use the parsing model and has quota left today."""
    try:
        from google import genai

        client = genai.Client(api_key=key)
        client.models.generate_content(model=model, contents="Reply with OK")
        return True
    except Exception as e:
        msg = str(e).replace(key, "***")
        if "PerDay" in msg:
            print(f"  ✗ {model}: daily quota already used up for this key's project "
                  "(a key from the same Google Cloud project shares the quota)")
        elif "NOT_FOUND" in msg or "PERMISSION_DENIED" in msg:
            print(f"  ✗ {model} is not available to this key's project: {msg[:120]}")
        else:
            print(f"  ✗ test call failed: {type(e).__name__}: {msg[:160]}")
        return False


def set_parse_key(lines: list[str], have: dict[str, str]) -> int:
    model = parse_model()
    print(f"Dedicated resume-parsing key → used first for resume extraction ({model}), never for anything else.")
    k = getpass.getpass("Parsing key (hidden): ").strip()
    if not k:
        print("No key entered; nothing changed.")
        return 1
    if k in have.values():
        print("  ! this key is already in the general pool; it adds no extra quota. Saving anyway.")
    if not (check(k) and check_generation(k, model)):
        print("Not saved.")
        return 1
    lines = [ln for ln in lines if not ln.strip().startswith(PARSE + "=")] + [f"{PARSE}={k}"]
    del k
    ENV.write_text("\n".join(lines).rstrip("\n") + "\n")
    os.chmod(ENV, stat.S_IRUSR | stat.S_IWUSR)
    print(f"  ✓ valid, quota available for {model}; saved as {PARSE} in .env (chmod 600).")
    print("Running apps pick it up automatically: open the candidate and press Retry parsing (Live API on).")
    return 0


def main() -> int:
    lines = read_env()
    have = existing(lines)
    if "--list" in sys.argv:
        has_parse = any(ln.strip().startswith(PARSE + "=") for ln in lines)
        print(f"{len(have)} key(s) configured: {', '.join(have) or 'none'}"
              f"{f' + {PARSE}' if has_parse else ''}")
        return 0
    if "--parse" in sys.argv:
        return set_parse_key(lines, have)
    if len(have) >= 4:
        print("4 keys already configured; remove some from .env first.")
        return 1
    print(f"{len(have)} key(s) configured. Paste each new key at the hidden prompt (Enter on empty = stop).")
    print("Use keys from DIFFERENT Google Cloud projects, or they share one quota.\n")
    values = set(have.values())
    added = 0
    while len(have) < 4:
        k = getpass.getpass(f"Key #{len(have) + 1} (hidden): ").strip()
        if not k:
            break
        if k in values:
            print("  ✗ duplicate key, skipped")
            continue
        if not check(k):
            continue
        name = "GEMINI_API_KEY" if "GEMINI_API_KEY" not in have else f"GEMINI_API_KEY_{len(have) + 1}"
        lines.append(f"{name}={k}")
        have[name] = k
        values.add(k)
        added += 1
        print(f"  ✓ valid, saved as {name}")
        del k
    ENV.write_text("\n".join(lines).rstrip("\n") + "\n")
    os.chmod(ENV, stat.S_IRUSR | stat.S_IWUSR)
    print(f"\nDone: {added} added, {len(have)} total. .env permissions set to 600.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
