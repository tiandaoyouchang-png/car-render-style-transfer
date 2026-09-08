from __future__ import annotations

import json
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

CACHE_ROOT = Path.home() / ".wondful_ai_renderer" / "cache"


@dataclass
class RenderSession:
    session_id: str
    directory: Path
    viewport_reference: Path
    prompt_file: Path
    output_raw: Path
    output_final: Path
    metadata_file: Path


def create_session() -> RenderSession:
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    sid = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    directory = CACHE_ROOT / sid
    directory.mkdir(parents=True, exist_ok=False)
    return RenderSession(
        session_id=sid,
        directory=directory,
        viewport_reference=directory / "camera_reference.png",
        prompt_file=directory / "prompt.txt",
        output_raw=directory / "output_raw.png",
        output_final=directory / "output.png",
        metadata_file=directory / "session.json",
    )


def save_metadata(session: RenderSession, data: dict) -> None:
    payload = dict(data)
    payload.setdefault("session_id", session.session_id)
    payload.setdefault("created_at", time.time())
    session.metadata_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_reference(src: str, session: RenderSession, name: str) -> str | None:
    if not src:
        return None
    p = Path(src)
    if not p.exists():
        return None
    suffix = p.suffix.lower() or ".png"
    dst = session.directory / f"{name}{suffix}"
    shutil.copy2(p, dst)
    return str(dst)


def copy_references(paths: list[str], session: RenderSession, prefix: str) -> list[str]:
    copied: list[str] = []
    for index, src in enumerate(paths, start=1):
        result = copy_reference(src, session, f"{prefix}_{index:02d}")
        if result:
            copied.append(result)
    return copied


def cleanup_old_sessions(max_sessions: int = 40, max_age_days: int = 14) -> None:
    if not CACHE_ROOT.exists():
        return
    dirs = [p for p in CACHE_ROOT.iterdir() if p.is_dir()]
    now = time.time()
    for p in dirs:
        try:
            if (now - p.stat().st_mtime) > max_age_days * 86400:
                shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass
    dirs = [p for p in CACHE_ROOT.iterdir() if p.is_dir()]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in dirs[max_sessions:]:
        shutil.rmtree(p, ignore_errors=True)
