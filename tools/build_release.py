"""Build the installable add-on ZIP: dist/Wondful-AI-Renderer-Blender-<version>.zip"""
import ast
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "wondful_ai_renderer"


def version() -> str:
    tree = ast.parse((PKG / "__init__.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "bl_info":
            info = ast.literal_eval(node.value)
            return ".".join(str(x) for x in info["version"])
    raise SystemExit("bl_info not found")


def main() -> None:
    out = ROOT / "dist" / f"Wondful-AI-Renderer-Blender-{version()}.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(PKG.rglob("*")):
            if path.is_dir() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
                continue
            zf.write(path, Path("wondful_ai_renderer") / path.relative_to(PKG))
    print(out)


if __name__ == "__main__":
    main()
