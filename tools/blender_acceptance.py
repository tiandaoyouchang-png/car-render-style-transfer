"""Headless Blender acceptance test for Wondful AI Renderer.

Run:
    blender -b --factory-startup --python tools/blender_acceptance.py -- --out /tmp/wondful_accept

On machines without a GPU, EEVEE cannot render headless; set
WONDFUL_STRUCTURE_ENGINE=CYCLES to render the structure passes on the CPU.
The script exits non-zero when any check fails and writes report.json.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

import bpy
import addon_utils

ROOT = Path(__file__).resolve().parents[1]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument("--out", default=str(Path(tempfile.gettempdir()) / "wondful_acceptance"))
parser.add_argument("--width", type=int, default=640)
parser.add_argument("--height", type=int, default=360)
args = parser.parse_args(argv)

OUT = Path(args.out)
shutil.rmtree(OUT, ignore_errors=True)
OUT.mkdir(parents=True, exist_ok=True)
report = {"blender": bpy.app.version_string, "engine_override": os.environ.get("WONDFUL_STRUCTURE_ENGINE", ""), "checks": {}}
failed = []


def check(name):
    def wrap(fn):
        t = time.time()
        try:
            info = fn()
            report["checks"][name] = {"ok": True, "sec": round(time.time() - t, 2), "info": info}
        except Exception as exc:
            failed.append(name)
            report["checks"][name] = {"ok": False, "sec": round(time.time() - t, 2), "error": repr(exc),
                                      "traceback": traceback.format_exc()[-2000:]}
        print(("PASS " if name not in failed else "FAIL ") + name, flush=True)
        return fn
    return wrap


# Install the add-on from this checkout into a throwaway scripts dir.
scripts = OUT / "_scripts" / "addons"
scripts.mkdir(parents=True)
shutil.copytree(ROOT / "wondful_ai_renderer", scripts / "wondful_ai_renderer")
sys.path.insert(0, str(scripts))


@check("enable_addon")
def _():
    mod = addon_utils.enable("wondful_ai_renderer", default_set=True, persistent=True)
    assert mod is not None, "addon_utils.enable returned None"
    assert hasattr(bpy.types.Scene, "wondful_ai"), "Scene.wondful_ai missing"
    return {"version": list(mod.bl_info["version"])}


def build_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    col = bpy.data.collections.new("Product")
    bpy.context.scene.collection.children.link(col)

    def add(op, name, **kw):
        op(**kw)
        o = bpy.context.active_object
        o.name = name
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
        return o

    body = add(bpy.ops.mesh.primitive_cube_add, "Body_Panel", size=1, location=(0, 0, 0.7))
    body.scale = (2.2, 0.9, 0.45)
    cabin = add(bpy.ops.mesh.primitive_cube_add, "Window_Glass", size=1, location=(-0.2, 0, 1.25))
    cabin.scale = (1.1, 0.8, 0.3)
    for i, (x, y) in enumerate([(1.4, 0.9), (1.4, -0.9), (-1.4, 0.9), (-1.4, -0.9)]):
        w = add(bpy.ops.mesh.primitive_cylinder_add, f"Wheel_Tire_{i}", radius=0.38, depth=0.25, location=(x, y, 0.38))
        w.rotation_euler = (1.5708, 0, 0)
    logo = add(bpy.ops.mesh.primitive_plane_add, "Logo_Badge", size=0.18, location=(2.21, 0, 0.8))
    logo.rotation_euler = (0, 1.5708, 0)
    plate = add(bpy.ops.mesh.primitive_plane_add, "License_Plate", size=1, location=(2.215, 0, 0.5))
    plate.scale = (0.26, 0.06, 1)
    plate.rotation_euler = (0, 1.5708, 0)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"
    bpy.ops.object.camera_add(location=(7.5, -5.5, 2.2), rotation=(1.35, 0, 0.94))
    bpy.context.scene.camera = bpy.context.active_object
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = args.width, args.height, 100
    sc.wondful_ai.product_collection = col
    return sc


scene = None


@check("build_scene")
def _():
    global scene
    scene = build_scene()
    return {"objects": len(bpy.data.objects)}


def user_render_state(sc):
    s = sc.render.image_settings
    return {
        "engine": sc.render.engine,
        "res": (sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage),
        "file_format": s.file_format,
        "media_type": getattr(s, "media_type", None),
        "filepath": sc.render.filepath,
        "scenes": sorted(x.name for x in bpy.data.scenes),
        "node_groups": sorted(x.name for x in bpy.data.node_groups),
        "pass_index": {o.name: o.pass_index for o in sc.objects},
    }


camera_base = OUT / "camera_base.png"
packets = {}


@check("camera_base_render")
def _():
    sc = bpy.context.scene
    prev = sc.render.engine
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 2
    sc.cycles.use_denoising = False
    sc.render.filepath = str(camera_base)
    bpy.ops.render.render(write_still=True)
    sc.render.engine = prev
    assert camera_base.is_file()
    return {"path": str(camera_base)}


for mode in ("STANDARD", "FAST"):
    @check(f"structure_packet_{mode.lower()}")
    def _(mode=mode):
        import numpy as np
        from wondful_ai_renderer.structure_packet import build_structure_packet
        sc = bpy.context.scene
        before = user_render_state(sc)
        pk = build_structure_packet(bpy.context, sc.wondful_ai, OUT / f"packet_{mode}",
                                    sc.render.resolution_x, sc.render.resolution_y,
                                    camera_base_path=str(camera_base), render_mode=mode)
        after = user_render_state(sc)
        assert before == after, f"user scene state changed: {before} -> {after}"
        assert pk.get("native_passes") is True, f"native passes failed: {pk.get('native_pass_error')}"
        assert pk.get("mask_source") == "NATIVE_OBJECT_INDEX_PASS", pk.get("mask_source")
        idx = np.load(pk["part_index_path"])
        assert idx.shape == (sc.render.resolution_y, sc.render.resolution_x), idx.shape
        names = pk["part_id_manifest"]
        visible = {n for n, meta in names.items() if (idx == meta["index"]).any()}
        for must in ("Body_Panel", "Logo_Badge", "License_Plate"):
            assert must in visible, f"{must} missing from Object Index"
        # Depth must not be saturated: product pixels need a real near/far spread.
        assert float(pk["depth_far"]) < 1e6, f"depth_far={pk['depth_far']} (background leaked into normalization)"
        depth_img = bpy.data.images.load(pk["depth_path"], check_existing=False)
        try:
            w, h = depth_img.size
            px = np.empty(w * h * 4, dtype=np.float32)
            depth_img.pixels.foreach_get(px)
            d = px.reshape(h, w, 4)[::-1, :, 0]
        finally:
            bpy.data.images.remove(depth_img)
        prod = d[np.load(pk["part_index_path"]) > 0]
        spread = float(np.percentile(prod, 95) - np.percentile(prod, 5))
        assert spread > 0.05, f"product depth spread {spread:.3f} (flat depth map)"
        packets[mode] = pk
        return {"depth_near": pk["depth_near"], "depth_far": pk["depth_far"], "product_depth_spread": round(spread, 3),
                "visible_parts": sorted(visible)}


@check("identity_preserve_mask")
def _():
    from wondful_ai_renderer.identity_preserve import build_identity_preserve_mask, write_identity_edit_mask
    pk = packets["STANDARD"]
    man = pk["part_id_manifest"]
    rows = [
        {"identity_critical": True, "part_id_index": man["Logo_Badge"]["index"], "part_class": "LOGO_BADGE"},
        {"identity_critical": True, "part_id_index": man["License_Plate"]["index"], "part_class": "PLATE"},
    ]
    meta = build_identity_preserve_mask(pk["part_index_path"], rows, OUT / "identity_mask.png", padding_px=2)
    assert meta["enabled"], meta
    assert meta["pixel_count"] > 0
    big = write_identity_edit_mask(OUT / "repair_mask.png", meta["mask_npy_path"],
                                   editable_region=(0.2, 0.2, 0.8, 0.8), output_size=(1536, 864))
    data = Path(big).read_bytes()
    size = (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))
    assert size == (1536, 864), size
    return {"pixel_count": meta["pixel_count"], "bbox": meta["bbox_normalized"], "repair_mask_size": size}


@check("hard_restore_roundtrip")
def _():
    from wondful_ai_renderer.identity_preserve import hard_restore_identity_pixels
    out = hard_restore_identity_pixels(camera_base, camera_base, OUT / "identity_mask.png", OUT / "restored.png")
    assert Path(out).is_file()
    return {"path": out}


@check("image_format_snapshot_restore")
def _():
    from wondful_ai_renderer import viewport_capture as vc
    s = bpy.context.scene.render.image_settings
    if hasattr(s, "media_type"):
        s.media_type = "MULTI_LAYER_IMAGE"
    s.file_format = "OPEN_EXR_MULTILAYER"
    snap = vc._snapshot_image_format(s)
    vc._set_png(s)
    assert s.file_format == "PNG"
    vc._restore_image_format(s, snap)
    assert s.file_format == "OPEN_EXR_MULTILAYER", s.file_format
    if hasattr(s, "media_type"):
        s.media_type = "IMAGE"
    s.file_format = "PNG"
    return snap


@check("unregister")
def _():
    addon_utils.disable("wondful_ai_renderer", default_set=True)
    assert not hasattr(bpy.types.Scene, "wondful_ai")
    return {}


report["failed"] = failed
(OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str))
print("ACCEPTANCE", "FAILED " + ",".join(failed) if failed else "PASSED", flush=True)
sys.exit(1 if failed else 0)
