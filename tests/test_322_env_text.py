"""3.2.2: environment references are read as text; only the clay canvas goes to the image model."""
import json, sys, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_316_regressions import load_package_module  # noqa: E402
CD = load_package_module("codex_direct")


class EnvTextPromptTests(unittest.TestCase):
    def test_simple_prompt_has_env_text_and_locks(self):
        text = CD.build_simple_prompt("雪山清晨", env_text="雪山公路，主光来自左侧。")
        self.assertIn("雪山公路，主光来自左侧。", text)
        self.assertIn("只出现描述里写到的元素", text)
        self.assertIn("坡度", text)
        self.assertNotIn("图 2", text)

    def test_describe_prompt_forbids_composition(self):
        self.assertIn("不要描述构图", CD.ENV_DESCRIBE_PROMPT)
        self.assertIn("不要出现", CD.ENV_DESCRIBE_PROMPT)

    def test_extract_text_from_sse(self):
        events = [json.dumps({"type": "response.output_text.delta", "delta": "雪山"}),
                  json.dumps({"type": "response.output_text.delta", "delta": "公路"}), "[DONE]"]
        self.assertEqual(CD.extract_text(events), "雪山公路")

    def test_describe_is_cached(self, tmp=None):
        import tempfile
        d = Path(tempfile.mkdtemp())
        img = d / "env.png"; img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        calls = []
        def fake_post(url, headers, payload, **kw):
            calls.append(payload)
            self.assertEqual(kw.get("want"), "text")
            self.assertEqual(payload["tools"], [])
            return "晴朗雪山"
        with mock.patch.object(CD, "post_responses", side_effect=fake_post), \
             mock.patch.object(CD, "auth_headers", return_value={}):
            t1, _ = CD.describe_environment([img], auth={}, auth_path=d / "a.json", cache_dir=str(d))
            t2, _ = CD.describe_environment([img], auth={}, auth_path=d / "a.json", cache_dir=str(d))
        self.assertEqual(t1, "晴朗雪山"); self.assertEqual(t2, "晴朗雪山")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()


def test_323_crest_ground_option_wired():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "wondful_ai_renderer"
    props = (root / "properties.py").read_text(encoding="utf-8")
    assert 'clay_ground: EnumProperty' in props and '"CREST", "山头"' in props
    assert 'clay_crest_angle: FloatProperty' in props
    ui = (root / "ui.py").read_text(encoding="utf-8")
    assert 'ground.prop(props, "clay_ground", expand=True)' in ui
    ops = (root / "operators.py").read_text(encoding="utf-8")
    assert 'ground=getattr(props, "clay_ground", "AUTO")' in ops
    vc = (root / "viewport_capture.py").read_text(encoding="utf-8")
    assert "def _crest_mesh(" in vc and 'ground_mode == "CREST"' in vc
    codex_direct = load_package_module("codex_direct")
    assert "坡顶" in codex_direct.build_simple_prompt("", env_text="雪山")
