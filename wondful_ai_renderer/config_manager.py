from __future__ import annotations

import json
import os
import stat
from pathlib import Path

CONFIG_DIR = Path.home() / ".wondful_ai_renderer"
STATS_FILE = CONFIG_DIR / "timings.json"


def _read_stats() -> dict:
    try:
        if STATS_FILE.exists():
            return json.loads(STATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_stats(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass
    tmp.replace(STATS_FILE)
    try:
        os.chmod(STATS_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def average_timing(kind: str, default: float) -> float:
    values = _read_stats().get(kind, [])
    values = [float(v) for v in values[-10:] if isinstance(v, (int, float)) and v > 0]
    if not values:
        return float(default)
    return sum(values) / len(values)


def record_timing(kind: str, seconds: float) -> None:
    if seconds <= 0:
        return
    data = _read_stats()
    values = list(data.get(kind, []))
    values.append(round(float(seconds), 3))
    data[kind] = values[-10:]
    _write_stats(data)
