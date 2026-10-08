"""3.1.9: four-step panel, one-button generate, Codex discovery (source-level checks)."""
import ast
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "wondful_ai_renderer"


class SimpleFlowTests(unittest.TestCase):
    def test_panel_steps(self):
        src = (PKG / "ui.py").read_text()
        for text in ("① 连接", "② 产品", "③ 场景", "wondful.generate", "\"高级\""):
            self.assertIn(text, src)
        ast.parse(src)

    def test_generate_operator_registered(self):
        init = (PKG / "__init__.py").read_text()
        self.assertGreaterEqual(init.count("WONDFUL_OT_generate"), 2)
        ops = (PKG / "operators.py").read_text()
        self.assertIn("def generate_needs_polish", ops)
        self.assertIn("pending_generate", ops)

    def test_codex_windows_candidates(self):
        src = (PKG / "codex_client.py").read_text()
        for text in ("NVM_SYMLINK", "openai.chatgpt-*", "Microsoft/WindowsApps", "codex.cmd"):
            self.assertIn(text, src)


if __name__ == "__main__":
    unittest.main()
