"""Config + small shared helpers."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


@lru_cache(maxsize=1)
def cfg() -> dict:
    _load_env()
    c = yaml.safe_load((ROOT / "config.yaml").read_text())
    c["llm"]["provider"] = os.environ.get("LLM_PROVIDER", c["llm"]["provider"])
    c["llm"]["model"] = os.environ.get("GEMINI_MODEL", c["llm"]["model"])
    if os.environ.get("HYT_OFFLINE") == "1":
        c["llm"]["offline"] = True
    if os.environ.get("HYT_PROFILE") == "v1.0":  # frozen, pre-registered headline system (make reproduce-v1.0)
        c["normalize"] = {**c.get("normalize", {}), "skills_file": "src/skills_v1_0.yaml"}
        c["decide"]["career_switch_blocking"] = True
        c["paths"]["results"] = "results/v1_0_reproduced"
    tuned = ROOT / c["paths"]["results"] / "thresholds.json"
    if tuned.exists() and os.environ.get("HYT_IGNORE_TUNED") != "1":
        c["decide"].update(json.loads(tuned.read_text()))
    return c


def path(key: str) -> Path:
    p = ROOT / cfg()["paths"][key]
    p.mkdir(parents=True, exist_ok=True)
    return p


def as_of() -> date:
    return date.fromisoformat(cfg()["as_of_date"])


def sha(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def read_json(p: Path):
    return json.loads(Path(p).read_text())
