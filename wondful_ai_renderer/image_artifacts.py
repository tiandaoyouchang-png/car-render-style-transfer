"""Accept new bitmap outputs; never mistake a reference or old attempt for a result."""
import time
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def is_bitmap(path):
    try:
        with Path(path).open("rb") as stream:
            header = stream.read(16)
        return (header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"\xff\xd8\xff")
                or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
                or header.startswith((b"BM", b"II*\x00", b"MM\x00*")))
    except OSError:
        return False


def _signature(path):
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


class ArtifactTracker:
    def __init__(self, workdir, excluded=()):
        self.workdir = Path(workdir).resolve()
        self.excluded = {Path(p).resolve() for p in excluded if p}
        self.before = {}
        for path in self.workdir.rglob("*"):
            try:
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                    self.before[path.resolve()] = _signature(path)
            except OSError:
                continue
        self.started_at = time.time()

    def accepts(self, path):
        try:
            path = Path(path).resolve()
            if path in self.excluded or not path.is_file() or not is_bitmap(path):
                return False
            signature = _signature(path)
            if path in self.before:
                return signature != self.before[path]
            # Some CLI tools write artifacts outside the session. Only accept an
            # explicit path returned by this invocation, with a recent timestamp.
            return path.is_relative_to(self.workdir) or path.stat().st_mtime + 2 >= self.started_at
        except OSError:
            return False

    def newest(self):
        candidates = [p for p in self.workdir.rglob("*")
                      if p.suffix.lower() in IMAGE_SUFFIXES and self.accepts(p)]
        return max(candidates, key=lambda p: p.stat().st_mtime_ns, default=None)
