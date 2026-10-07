"""Fail CI on real undefined names (the class of bug behind the 3.1.2-3.1.5
AGY NameError).  Blender property annotations such as
``prop: StringProperty(name="提示词", options={'HIDDEN'})`` are parsed by
pyflakes as string annotations and produce false positives, so warnings on
lines that belong to a bpy property declaration are ignored."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["wondful_ai_renderer", "tests", "tools"]
PROPERTY_HINT = re.compile(r"Property\(|options\s*=|subtype\s*=|items\s*=|name\s*=|description\s*=|default\s*=|\(\s*['\"][A-Z_]+['\"]\s*,")


def _in_property_call(lines, lineno):
    # Walk upward to the statement start; a bpy property declaration contains "Property(".
    for i in range(lineno - 1, max(-1, lineno - 40), -1):
        text = lines[i]
        if "Property(" in text:
            return True
        if re.match(r"^\s*(def |class |@)", text) or (i < lineno - 1 and text.strip() == ""):
            return False
    return False


def main() -> int:
    proc = subprocess.run([sys.executable, "-m", "pyflakes", *TARGETS], cwd=ROOT, capture_output=True, text=True)
    failures = []
    cache = {}
    for line in proc.stdout.splitlines():
        if "undefined name" not in line:
            continue
        path, lineno, *_ = line.split(":", 3)
        lines = cache.setdefault(path, (ROOT / path).read_text(encoding="utf-8").splitlines())
        if _in_property_call(lines, int(lineno)):
            continue
        failures.append(line)
    for f in failures:
        print(f)
    print(f"undefined-name check: {len(failures)} real issue(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
