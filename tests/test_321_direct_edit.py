"""3.2.1: Codex 图像编辑（直连）— payload, SSE parsing, auth refresh and fallback (mock backend)."""
import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_316_regressions import load_package_module  # noqa: E402
import mock_codex_backend as mock  # noqa: E402

direct = load_package_module("codex_direct")
identity = load_package_module("identity_preserve")
composition = load_package_module("composition")
PKG = Path(__file__).resolve().parents[1] / "wondful_ai_renderer"


def rgb_png(path, w, h, rgb=(200, 200, 200)):
    Path(path).write_bytes(mock.solid_png(w, h, rgb))
    return str(path)


def jpeg_named_png(path):
    # A JPEG payload behind a .png name (providers do this); only the header matters here.
    Path(path).write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 64)
    return str(path)


class DirectEditTestBase(unittest.TestCase):
    mode = "ok"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="wondful321_"))
        self.server, self.state = mock.start_server(self.mode)
        port = self.server.server_address[1]
        self.env_backup = {k: os.environ.get(k) for k in ("CODEX_HOME", direct.BASE_URL_ENV, direct.REFRESH_URL_ENV, "USERPROFILE", "no_proxy", "NO_PROXY")}
        os.environ["no_proxy"] = os.environ["NO_PROXY"] = "127.0.0.1,localhost"
        os.environ["CODEX_HOME"] = str(self.tmp)
        os.environ.pop("USERPROFILE", None)
        os.environ[direct.BASE_URL_ENV] = f"http://127.0.0.1:{port}/backend-api/codex"
        os.environ[direct.REFRESH_URL_ENV] = f"http://127.0.0.1:{port}/oauth/token"
        self.access = mock.write_fake_auth(self.tmp / "auth.json")
        self.camera = rgb_png(self.tmp / "camera_base.png", 1600, 900)
        self.product = rgb_png(self.tmp / "product.png", 600, 300, (10, 120, 60))
        self.env = jpeg_named_png(self.tmp / "env.png")
        self.structure = rgb_png(self.tmp / "structure_mask.png", 1600, 900, (255, 0, 0))
        self.manifest = [
            {"path": self.camera, "members": [{"reference": 1, "role": "camera", "path": self.camera}]},
            {"path": self.structure, "members": [{"reference": 2, "role": "structure", "sub_role": "mask", "path": self.structure}]},
            {"path": self.product, "members": [{"reference": 3, "role": "product", "path": self.product}]},
            {"path": self.env, "members": [{"reference": 4, "role": "environment", "path": self.env}]},
        ]
        self.refs = [self.camera, self.structure, self.product, self.env]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        for k, v in self.env_backup.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def edit(self, **kw):
        args = dict(prompt="雪山公路清晨，冷色调", edit_base_path=self.camera, reference_paths=self.refs,
                    output_path=str(self.tmp / "out.png"), size=direct.choose_edit_size(1600, 900, 2048),
                    manifest=self.manifest, log_dir=str(self.tmp), tag="t1", client_version="codex-cli 0.48.0")
        args.update(kw)
        return direct.edit_image(**args)


class PayloadTests(DirectEditTestBase):
    def test_payload_shape_headers_and_output(self):
        result = self.edit()
        self.assertEqual(result["engine"], "codex_direct_edit")
        self.assertEqual(self.state.response_calls, 1)
        req = [r for r in self.state.requests if r["path"].endswith("/responses")][0]
        h = {k.lower(): v for k, v in req["headers"].items()}
        self.assertEqual(h["chatgpt-account-id"], "acct_test_123")
        self.assertEqual(h["originator"], "codex_cli_rs")
        self.assertEqual(h["accept"], "text/event-stream")
        self.assertEqual(h["version"], "0.48.0")
        self.assertTrue(h["authorization"].startswith("Bearer <redacted"))
        body = self.state.raw_bodies[0]
        self.assertEqual(body["tool_choice"], {"type": "image_generation"})
        self.assertTrue(body["stream"])
        self.assertFalse(body["store"])
        self.assertEqual(body["model"], direct.DEFAULT_MODEL)
        tool = body["tools"][0]
        self.assertEqual(tool["type"], "image_generation")
        self.assertEqual(tool["model"], "gpt-image-2")
        self.assertEqual(tool["size"], "2048x1152")
        self.assertNotIn("input_image_mask", tool)
        content = body["input"][0]["content"]
        self.assertEqual(content[0]["type"], "input_text")
        images = [c for c in content if c["type"] == "input_image"]
        self.assertEqual(len(images), 4)
        # image 1 is the camera base, byte for byte
        first = base64.b64decode(images[0]["image_url"].split(",", 1)[1])
        self.assertEqual(first, Path(self.camera).read_bytes())
        self.assertTrue(images[3]["image_url"].startswith("data:image/jpeg;base64,"))
        self.assertIn("图 1 是编辑画布", content[0]["text"])
        self.assertIn("图 3：产品三视图", content[0]["text"])
        out = Path(result["source"])
        self.assertEqual(composition.image_dimensions(out), (2048, 1152))
        # diagnostics log written, no secrets inside
        log = (self.tmp / "codex_direct_t1.json").read_text(encoding="utf-8")
        self.assertNotIn(self.access, log)
        self.assertNotIn("REFRESH-SECRET", log)
        self.assertNotIn("acct_test_123", log)
        self.assertIn("<redacted>", log)

    def test_repair_mask_and_order(self):
        candidate = rgb_png(self.tmp / "cand.png", 2048, 1152, (40, 90, 160))
        mask = composition.write_repair_mask(self.tmp / "repair_mask.png", (2048, 1152), (0.2, 0.3, 0.7, 0.9))
        result = self.edit(edit_base_path=candidate, mask_path=mask, repair=True)
        self.assertTrue(result["mask"])
        body = self.state.raw_bodies[0]
        tool = body["tools"][0]
        mask_url = tool["input_image_mask"]["image_url"]
        self.assertTrue(mask_url.startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(mask_url.split(",", 1)[1]), Path(mask).read_bytes())
        images = [c for c in body["input"][0]["content"] if c["type"] == "input_image"]
        self.assertEqual(base64.b64decode(images[0]["image_url"].split(",", 1)[1]), Path(candidate).read_bytes())
        self.assertEqual(base64.b64decode(images[1]["image_url"].split(",", 1)[1]), Path(self.camera).read_bytes())
        self.assertEqual(len(images), 5)
        self.assertIn("上一轮候选图", body["input"][0]["content"][0]["text"])

    def test_mask_resampled_to_base_size(self):
        npy = self.tmp / "identity.npy"
        ident = np.zeros((450, 800), dtype=bool)
        ident[100:120, 200:260] = True
        np.save(npy, ident)
        mask = identity.write_identity_edit_mask(self.tmp / "identity_edit_mask.png", npy)
        result = self.edit(mask_path=mask)
        self.assertIn("1600×900", result["mask_note"])
        tool = self.state.raw_bodies[0]["tools"][0]
        data = base64.b64decode(tool["input_image_mask"]["image_url"].split(",", 1)[1])
        resized = self.tmp / "sent_mask.png"
        resized.write_bytes(data)
        rgba = direct.read_png_rgba(resized)
        self.assertEqual(rgba.shape, (900, 1600, 4))
        self.assertEqual(int(rgba[210, 450, 3]), 255)  # identity preserved (opaque)
        self.assertEqual(int(rgba[10, 10, 3]), 0)      # editable (transparent)

    def test_five_image_limit_drops_structure_first(self):
        person = rgb_png(self.tmp / "person.png", 300, 300)
        env2 = rgb_png(self.tmp / "env2.png", 300, 300)
        manifest = self.manifest + [
            {"path": person, "members": [{"reference": 5, "role": "person", "path": person}]},
            {"path": env2, "members": [{"reference": 6, "role": "environment", "path": env2}]},
        ]
        images, dropped = direct.select_images(self.camera, self.refs + [person, env2], manifest)
        self.assertEqual(len(images), 5)
        self.assertEqual([r for _p, r in dropped], ["structure"])
        self.assertEqual(images[0][1], "camera")

    def test_choose_size_limits(self):
        for (w, h, edge) in [(1600, 900, 2048), (1080, 1920, 2048), (1000, 1000, 1024), (4000, 1000, 4096), (1920, 1080, 1280)]:
            size = direct.choose_edit_size(w, h, edge)
            sw, sh = map(int, size.split("x"))
            self.assertEqual(sw % 16, 0)
            self.assertEqual(sh % 16, 0)
            self.assertLessEqual(max(sw, sh), 3840)
            self.assertTrue(655360 <= sw * sh <= 8294400, size)
            if max(w, h) / min(w, h) <= 3:
                self.assertLess(abs((sw / sh) / (w / h) - 1), 0.01, size)

    def test_sse_parser_variants(self):
        b64 = base64.b64encode(mock.solid_png(32, 32)).decode()
        stream = [
            "event: response.created\n", 'data: {"type":"response.created","response":{"id":"r9"}}\n', "\n",
            ": keepalive\n", "\n",
            "event: response.completed\n",
            'data: {"type":"response.completed","response":{"id":"r9","output":[{"type":"image_generation_call","status":"completed","result":"%s"}]}}\n' % b64,
            "\n", "data: [DONE]\n", "\n",
        ]
        got, _item, rid = direct.extract_image(direct.parse_sse_events(stream))
        self.assertEqual(got, b64)
        self.assertEqual(rid, "r9")
        with self.assertRaises(direct.DirectEditError):
            direct.extract_image(direct.parse_sse_events(['data: {"type":"response.failed","response":{"error":{"code":"server_error"}}}\n', "\n"]))


class RefreshTests(DirectEditTestBase):
    mode = "401_then_ok"

    def test_401_refreshes_and_writes_back(self):
        result = self.edit()
        self.assertEqual(result["engine"], "codex_direct_edit")
        self.assertEqual(self.state.token_calls, 1)
        saved = json.loads((self.tmp / "auth.json").read_text())
        self.assertEqual(saved["tokens"]["refresh_token"], "REFRESH-SECRET-2")
        token_req = [r for r in self.state.requests if r["path"].endswith("/oauth/token")][0]
        self.assertEqual(token_req["grant"], "refresh_token")
        self.assertEqual(token_req["client_id"], direct.CODEX_CLIENT_ID)

    def test_expired_token_refreshed_before_call(self):
        mock.write_fake_auth(self.tmp / "auth.json", exp_offset=-10)
        self.edit()
        self.assertEqual(self.state.token_calls, 1)
        self.assertEqual(self.state.response_calls, 1)


class CompatTests(DirectEditTestBase):
    mode = "400_then_ok"

    def test_400_retries_lean_payload(self):
        result = self.edit()
        self.assertTrue(result["compat_payload"])
        self.assertNotIn("model", self.state.raw_bodies[-1]["tools"][0])


class JsonBodyTests(DirectEditTestBase):
    mode = "json"

    def test_non_stream_json_response(self):
        result = self.edit()
        self.assertEqual(result["status"], "ok")


class FallbackTests(DirectEditTestBase):
    mode = "404"

    def _fallback(self, **kwargs):
        self.fallback_calls.append(kwargs)
        Path(kwargs["output_path"]).write_bytes(mock.solid_png(64, 36))
        return {"engine": "codex_oauth_imagegen", "status": "ok"}

    def test_endpoint_failure_falls_back_and_disables(self):
        self.fallback_calls = []
        state, phases = {}, []
        kwargs = dict(prompt="p" + "\n\n【图像工具输入清单】x", reference_paths=self.refs, output_path=str(self.tmp / "o1.png"),
                      cwd=str(self.tmp), explicit_path="", model="", edit_base_path=self.camera, edit_mask_path="",
                      structure_control=None, timeout=60)
        r1 = direct.generate_with_fallback(dict(kwargs), fallback=self._fallback, state=state, size="2048x1152",
                                           manifest=self.manifest, bundle_note="\n\n【图像工具输入清单】x",
                                           on_status=phases.append)
        self.assertEqual(r1["engine"], "codex_oauth_imagegen")
        self.assertIn("404", r1["direct_fallback_reason"])
        self.assertTrue(state["disabled"])
        self.assertTrue(phases and "改用 Codex 代理生成" in phases[0])
        # the agent fallback still receives the original prompt (with its bundle note)
        self.assertIn("【图像工具输入清单】", self.fallback_calls[0]["prompt"])
        calls_before = self.state.response_calls
        kwargs["output_path"] = str(self.tmp / "o2.png")
        direct.generate_with_fallback(dict(kwargs), fallback=self._fallback, state=state, size="2048x1152")
        self.assertEqual(self.state.response_calls, calls_before)  # skipped after a fatal error
        self.assertIn("改用 Codex 代理生成", direct.engine_note(state))

    def test_missing_auth_falls_back(self):
        self.fallback_calls = []
        (self.tmp / "auth.json").unlink()
        os.environ["CODEX_HOME"] = str(self.tmp / "nowhere")
        state = {}
        home_auth = Path.home() / ".codex" / "auth.json"
        if home_auth.exists():
            self.skipTest("a real ~/.codex/auth.json exists on this machine")
        r = direct.generate_with_fallback(dict(prompt="p", reference_paths=self.refs, output_path=str(self.tmp / "o.png"),
                                               cwd=str(self.tmp), edit_base_path=self.camera, timeout=60),
                                          fallback=self._fallback, state=state, size="2048x1152")
        self.assertEqual(r["engine"], "codex_oauth_imagegen")
        self.assertIn("auth.json", state["disabled"])
        self.assertEqual(self.state.response_calls, 0)


class ServerErrorTests(DirectEditTestBase):
    mode = "500"

    def test_5xx_falls_back_without_disabling(self):
        state = {}
        calls = []

        def fb(**kw):
            calls.append(1)
            return {"engine": "codex_oauth_imagegen"}
        direct.generate_with_fallback(dict(prompt="p", reference_paths=self.refs, output_path=str(self.tmp / "o.png"),
                                           cwd=str(self.tmp), edit_base_path=self.camera, timeout=60),
                                      fallback=fb, state=state, size="2048x1152")
        self.assertEqual(calls, [1])
        self.assertFalse(state["disabled"])  # transient: the next attempt tries direct again


class WiringTests(unittest.TestCase):
    def test_operator_and_ui_wiring(self):
        ops = (PKG / "operators.py").read_text(encoding="utf-8")
        self.assertIn("codex_direct.generate_with_fallback", ops)
        self.assertIn('provider["id"] == "codex" and bool(getattr(prefs, "codex_direct_edit", True))', ops)
        props = (PKG / "properties.py").read_text(encoding="utf-8")
        self.assertIn("codex_direct_edit: BoolProperty", props)
        self.assertIn("last_engine_note: StringProperty", props)
        ui = (PKG / "ui.py").read_text(encoding="utf-8")
        adv = ui[ui.index("# ---- 高级"):]
        self.assertIn('"codex_direct_edit"', adv)  # the toggle lives under 高级
        agy = (PKG / "antigravity_client.py").read_text(encoding="utf-8")
        self.assertNotIn("codex_direct", agy)

    def test_no_heavy_deps(self):
        src = (PKG / "codex_direct.py").read_text(encoding="utf-8")
        for mod in ("requests", "PIL", "httpx", "aiohttp"):
            self.assertNotIn(f"import {mod}", src)
        self.assertNotIn("import bpy", src)


if __name__ == "__main__":
    unittest.main()
