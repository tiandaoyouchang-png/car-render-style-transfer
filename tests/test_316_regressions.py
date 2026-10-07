"""Regression tests for Wondful 3.1.6 (pure Python, no Blender required)."""
import importlib.util
import json
import os
import stat
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "wondful_ai_renderer"


def load_package_module(name):
    """Import a submodule without running the package __init__ (which needs bpy)."""
    pkg_name = "wondful_ai_renderer_316test"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(PKG_DIR)]
        sys.modules[pkg_name] = pkg
    full = f"{pkg_name}.{name}"
    if full in sys.modules:
        return sys.modules[full]
    spec = importlib.util.spec_from_file_location(full, PKG_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[full] = module
    spec.loader.exec_module(module)
    return module


identity = load_package_module("identity_preserve")


FAKE_AGY = textwrap.dedent(
    r'''
    #!/usr/bin/env python3
    import json, os, struct, sys, zlib
    out = os.path.join(os.getcwd(), "agy_generated.png")
    w, h = 32, 18
    raw = b"".join(b"\x00" + b"\x80\x80\x80\xff" * w for _ in range(h))
    def ch(k, d):
        return struct.pack(">I", len(d)) + k + d + struct.pack(">I", zlib.crc32(k + d) & 0xffffffff)
    with open(out, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b""))
    print(json.dumps({"event": "step_update", "conversation_id": "conv-316",
                      "step_update": {"step_type": "tool", "tool_name": "generate_image",
                                      "tool_info": {"output": {"path": out}}}}))
    print(json.dumps({"status": "SUCCESS", "response": "WONDFUL_ANTIGRAVITY_IMAGEGEN_OK",
                      "conversation_id": "conv-316"}))
    '''
).lstrip()


@unittest.skipIf(os.name == "nt", "fake CLI uses a POSIX shebang")
class AntigravitySuccessPathTests(unittest.TestCase):
    """3.1.2-3.1.5 raised NameError('conversation_ids') after AGY produced an image."""

    def test_generate_image_success_returns_result_not_nameerror(self):
        agy = load_package_module("antigravity_client")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cli = tmp / "agy"
            cli.write_text(FAKE_AGY)
            cli.chmod(cli.stat().st_mode | stat.S_IEXEC)
            ref = tmp / "camera_base.png"
            identity.write_gray_png(ref, np.zeros((18, 32), dtype=np.uint8))
            target = tmp / "output_candidate_v01_a01.png"
            result = agy.generate_image(
                prompt="studio car", reference_paths=[str(ref)], output_path=str(target),
                cwd=str(tmp), explicit_path=str(cli), model="", timeout=60,
            )
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["conversation_id"], "conv-316")
            self.assertTrue(target.is_file())


class IdentityRepairMaskSizeTests(unittest.TestCase):
    """Strict repair pairs the identity mask with the previous candidate, whose size
    can differ from the Camera Base grid."""

    def _read_png_size(self, path):
        data = Path(path).read_bytes()
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")

    def test_repair_mask_matches_candidate_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            mask = np.zeros((360, 640), dtype=np.uint8)
            mask[150:170, 470:480] = 1  # a small logo
            npy = tmp / "identity.npy"
            np.save(npy, mask)
            out = identity.write_identity_edit_mask(
                tmp / "repair.png", npy, editable_region=(0.2, 0.2, 0.8, 0.8), output_size=(1536, 864)
            )
            self.assertEqual(self._read_png_size(out), (1536, 864))

    def test_logo_survives_downscale(self):
        mask = np.zeros((864, 1536), dtype=bool)
        mask[400:402, 1000:1100] = True  # 2px-tall stroke
        small = identity.resize_mask_nearest(mask, 384, 216)
        self.assertEqual(small.shape, (216, 384))
        self.assertTrue(small.any())

    def test_identity_mapped_to_same_normalized_location(self):
        mask = np.zeros((360, 640), dtype=bool)
        mask[180:190, 320:330] = True
        big = identity.resize_mask_nearest(mask, 1280, 720)
        ys, xs = np.nonzero(big)
        self.assertAlmostEqual(xs.mean() / 1280, (320 + 4.5) / 640, places=2)
        self.assertAlmostEqual(ys.mean() / 720, (180 + 4.5) / 360, places=2)

    def test_default_size_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            npy = Path(tmp) / "identity.npy"
            np.save(npy, np.zeros((90, 160), dtype=np.uint8))
            out = identity.write_identity_edit_mask(Path(tmp) / "m.png", npy)
            self.assertEqual(self._read_png_size(out), (160, 90))


class StructurePacketSourceTests(unittest.TestCase):
    """Static guards for Blender 5.x compatibility (structure_packet imports bpy)."""

    @classmethod
    def setUpClass(cls):
        cls.src = (PKG_DIR / "structure_packet.py").read_text(encoding="utf-8")

    def test_no_unguarded_scene_node_tree(self):
        self.assertIn("compositing_node_group", self.src)
        self.assertNotIn("temp_scene.node_tree.nodes", self.src)

    def test_object_index_socket_alias(self):
        self.assertIn('"Object Index"', self.src)

    def test_eevee_identifier_fallback(self):
        self.assertIn('"BLENDER_EEVEE"', self.src)

    def test_depth_background_excluded(self):
        self.assertIn("_depth_background_cutoff", self.src)
        self.assertNotIn("(depth < 1e20)", self.src)


if __name__ == "__main__":
    unittest.main()
