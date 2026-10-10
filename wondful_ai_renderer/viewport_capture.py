from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Tuple

import bpy

from .composition import image_dimensions


def find_view3d(context):
    if context.area and context.area.type == "VIEW_3D":
        area = context.area
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        space = area.spaces.active
        if region:
            return context.window, area, region, space

    window = context.window
    if window and window.screen:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                region = next((r for r in area.regions if r.type == "WINDOW"), None)
                if region:
                    return window, area, region, area.spaces.active
    raise RuntimeError("未找到可用的 Blender 3D Viewport。请确保当前窗口中存在 3D View。")


def viewport_dimensions(context) -> Tuple[int, int]:
    _window, _area, region, _space = find_view3d(context)
    return int(region.width), int(region.height)


def camera_output_dimensions(context) -> Tuple[int, int]:
    """Return the scene's effective camera/output dimensions.

    The final AI canvas follows Render Properties resolution rather than the
    3D Viewport/N-panel size.
    """
    render = context.scene.render
    pct = max(1, int(render.resolution_percentage)) / 100.0
    width = max(1, int(round(int(render.resolution_x) * pct)))
    height = max(1, int(round(int(render.resolution_y) * pct)))
    return width, height


def require_scene_camera(context):
    camera = getattr(context.scene, "camera", None)
    if camera is None:
        raise RuntimeError("当前 Scene 没有活动 Camera。请先设置 Scene Camera 后再进行 AI 渲染。")
    return camera


def _capture_framebuffer(window, region, filepath: str) -> bool:
    """Compatibility helper for the legacy viewport-capture path."""
    if not hasattr(window, "screenshot"):
        return False
    try:
        import imbuf

        rect = ((region.x, region.y), (region.x + region.width, region.y + region.height))
        pixels = window.screenshot(region=rect, use_alpha=False)
        height, width = pixels.shape[0], pixels.shape[1]
        ibuf = imbuf.new((width, height))
        ibuf.file_type = "PNG"
        if not hasattr(ibuf, "with_buffer"):
            return False
        with ibuf.with_buffer(write=True) as buf:
            buf.cast("B")[:] = pixels.cast("B")
        imbuf.write(ibuf, filepath=filepath)
        ibuf.free()
        return Path(filepath).exists()
    except Exception:
        return False


def _snapshot_image_format(settings) -> dict:
    """Blender 5.x adds ``media_type``; EXR multilayer lives under MULTI_LAYER_IMAGE
    and PNG cannot be assigned until media_type is IMAGE.  Save both so the user's
    Output Properties are restored exactly."""
    return {
        "media_type": getattr(settings, "media_type", None),
        "file_format": settings.file_format,
    }


def _set_png(settings) -> None:
    if getattr(settings, "media_type", None) not in (None, "IMAGE"):
        settings.media_type = "IMAGE"
    settings.file_format = "PNG"


def _restore_image_format(settings, snap: dict) -> None:
    try:
        if snap.get("media_type") is not None and getattr(settings, "media_type", None) != snap["media_type"]:
            settings.media_type = snap["media_type"]
        settings.file_format = snap["file_format"]
    except Exception:
        pass


def _capture_opengl_view(context, window, area, region, filepath: str) -> bool:
    """Legacy active-view capture retained as a fallback utility."""
    scene = context.scene
    render = scene.render
    old_path = render.filepath
    old_x, old_y, old_pct = render.resolution_x, render.resolution_y, render.resolution_percentage
    old_format = _snapshot_image_format(render.image_settings)
    try:
        render.filepath = filepath
        render.resolution_x = max(1, int(region.width))
        render.resolution_y = max(1, int(region.height))
        render.resolution_percentage = 100
        _set_png(render.image_settings)
        with context.temp_override(window=window, area=area, region=region, scene=scene):
            result = bpy.ops.render.opengl(animation=False, sequencer=False, write_still=True, view_context=True)
        return "FINISHED" in result and Path(filepath).exists()
    finally:
        render.filepath = old_path
        render.resolution_x, render.resolution_y = old_x, old_y
        render.resolution_percentage = old_pct
        _restore_image_format(render.image_settings, old_format)


def _capture_camera_opengl(context, filepath: str) -> bool:
    """Capture exactly the active Scene Camera frame using Blender's OpenGL render.

    `view_context=False` makes the OpenGL render use the Scene Camera rather than
    the arbitrary interactive viewport framing. We temporarily normalize the
    effective render size so the output bitmap has the same X/Y ratio and pixel
    dimensions the user configured in Output Properties.
    """
    scene = context.scene
    require_scene_camera(context)
    width, height = camera_output_dimensions(context)
    window, area, region, _space = find_view3d(context)

    render = scene.render
    old_path = render.filepath
    old_x, old_y, old_pct = render.resolution_x, render.resolution_y, render.resolution_percentage
    old_format = _snapshot_image_format(render.image_settings)
    old_color_mode = getattr(render.image_settings, "color_mode", None)
    frame_options = {key: getattr(render, key) for key in ("use_border", "use_crop_to_border", "use_compositing", "use_sequencer", "use_multiview") if hasattr(render, key)}
    try:
        for key in frame_options:
            setattr(render, key, False)
        render.filepath = filepath
        render.resolution_x = width
        render.resolution_y = height
        render.resolution_percentage = 100
        _set_png(render.image_settings)
        try:
            render.image_settings.color_mode = "RGB"
        except Exception:
            pass

        with context.temp_override(window=window, area=area, region=region, scene=scene):
            result = bpy.ops.render.opengl(animation=False, sequencer=False, write_still=True, view_context=False)
        return "FINISHED" in result and Path(filepath).exists()
    finally:
        render.filepath = old_path
        render.resolution_x, render.resolution_y = old_x, old_y
        render.resolution_percentage = old_pct
        _restore_image_format(render.image_settings, old_format)
        for key, value in frame_options.items():
            setattr(render, key, value)
        if old_color_mode is not None:
            try:
                render.image_settings.color_mode = old_color_mode
            except Exception:
                pass


def capture_camera_reference(context, filepath: str) -> tuple[int, int, str]:
    """Capture the current Scene Camera frame as the sole composition reference.

    Returns (width, height, method). The camera/output frame is intentionally
    independent from the visible 3D Viewport or sidebar dimensions.
    """
    filepath = str(Path(filepath))
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    width, height = camera_output_dimensions(context)
    require_scene_camera(context)
    if context.scene.camera.data.type not in {"PERSP", "ORTHO"}:
        raise RuntimeError("当前构图控制支持透视或正交相机，请使用 PERSP / ORTHO 相机。")
    render = context.scene.render
    if abs(float(render.pixel_aspect_x) / float(render.pixel_aspect_y) - 1.0) > 1e-6:
        raise RuntimeError("AI 图像使用方形像素，请先把输出的像素宽高比设为 1:1。")
    if _capture_camera_opengl(context, filepath):
        actual = image_dimensions(filepath)
        if actual != (width, height):
            raise RuntimeError(f"相机捕获尺寸异常：期望 {width}×{height}，实际 {actual}；已停止提交，避免结构图错位。")
        return width, height, "CAMERA_OPENGL_FULL_FRAME"
    raise RuntimeError("无法捕获当前 Scene Camera Frame。请确认 Scene Camera 有效，并在 3D Viewport 中重试。")


def capture_active_viewport(context, filepath: str) -> tuple[int, int, str]:
    """Legacy capture helper kept for compatibility with older sessions/tools."""
    filepath = str(Path(filepath))
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    window, area, region, _space = find_view3d(context)
    width, height = int(region.width), int(region.height)

    if _capture_framebuffer(window, region, filepath):
        return width, height, "FRAMEBUFFER"
    if _capture_opengl_view(context, window, area, region, filepath):
        return width, height, "OPENGL"
    raise RuntimeError("无法捕获当前 3D Viewport。")


def _product_floor_z(collection):
    from mathutils import Vector
    zs = []
    objs = list(collection.all_objects) if collection else [o for o in bpy.context.scene.objects]
    for obj in objs:
        if obj.type != "MESH" or obj.hide_render:
            continue
        for corner in obj.bound_box:
            zs.append((obj.matrix_world @ Vector(corner)).z)
    return min(zs) if zs else 0.0


LAST_CLAY_INFO = {}


def _product_up_axis(collection):
    """World-space 'up' of the product: Z axis of its root object(s).

    When the user tilts the car onto a slope by rotating its root/parent, the
    temporary floor follows that tilt so the wheels still sit on the ground.
    """
    from mathutils import Vector
    if not collection:
        return Vector((0.0, 0.0, 1.0))
    objs = list(collection.all_objects)
    members = set(objs)
    roots = [o for o in objs if o.parent is None or o.parent not in members]
    axes = []
    for root in roots:
        top = root
        while top.parent is not None:  # parented to an empty outside the collection
            top = top.parent
        axis = (top.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0)))
        if axis.length > 1e-6:
            axes.append(axis.normalized())
    if not axes:
        return Vector((0.0, 0.0, 1.0))
    ref = axes[0]
    agree = [a for a in axes if a.dot(ref) > 0.995]
    if len(agree) < max(1, len(axes) // 2):
        return Vector((0.0, 0.0, 1.0))  # roots disagree: keep world up
    up = sum(agree, Vector()) / len(agree)
    up.normalize()
    return up if up.z > 0.2 else Vector((0.0, 0.0, 1.0))


def _product_bounds(collection):
    from mathutils import Vector
    pts = []
    objs = list(collection.all_objects) if collection else [o for o in bpy.context.scene.objects]
    for obj in objs:
        if obj.type != "MESH" or obj.hide_render:
            continue
        pts += [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return pts


def _user_ground(context, collection, product_pts):
    """Return a mesh object of the user's own that forms ground under the product, else None."""
    from mathutils import Vector
    if not product_pts:
        return None
    members = set(collection.all_objects) if collection else set()
    xs = [p.x for p in product_pts]; ys = [p.y for p in product_pts]; zs = [p.z for p in product_pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    foot = max(max(xs) - min(xs), max(ys) - min(ys), 1e-3)
    bottom = min(zs)
    for obj in context.scene.objects:
        if obj in members or obj.type != "MESH" or obj.hide_render or obj.name.startswith("_wondful_"):
            continue
        try:
            if not obj.visible_get():
                continue
        except Exception:
            pass
        bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        bx = [p.x for p in bb]; by = [p.y for p in bb]; bz = [p.z for p in bb]
        if not (min(bx) <= cx <= max(bx) and min(by) <= cy <= max(by)):
            continue
        if max(max(bx) - min(bx), max(by) - min(by)) < 1.5 * foot:
            continue
        if min(bz) > bottom + 0.05 * foot:
            continue  # starts above the wheels: not a ground
        return obj
    return None


def render_clay_base(context, filepath: str, collection=None) -> bool:
    """Render the Scene Camera with a temporary floor, sun and light-gray world.

    This is the edit canvas for the simple direct-edit path: a lit clay render
    with ground contact gives the image model a photographic starting point, so
    it repaints materials and environment instead of re-composing the shot.
    Everything temporary is removed afterwards; the user's scene is unchanged.
    """
    scene = context.scene
    require_scene_camera(context)
    width, height = camera_output_dimensions(context)
    render = scene.render
    snap = {
        "engine": render.engine, "filepath": render.filepath, "x": render.resolution_x, "y": render.resolution_y,
        "pct": render.resolution_percentage, "fmt": _snapshot_image_format(render.image_settings),
        "world": scene.world, "film": getattr(render, "film_transparent", False),
    }
    frame_options = {k: getattr(render, k) for k in ("use_border", "use_crop_to_border", "use_compositing", "use_sequencer") if hasattr(render, k)}
    created = []
    try:
        from mathutils import Vector
        pts = _product_bounds(collection)
        ground = _user_ground(context, collection, pts)
        up = _product_up_axis(collection)
        slope = math.degrees(math.acos(max(-1.0, min(1.0, up.z))))
        LAST_CLAY_INFO.clear()
        LAST_CLAY_INFO.update({"user_ground": ground.name if ground else "", "slope_deg": round(slope, 1)})
        mesh = bpy.data.meshes.new("_wondful_clay_floor")
        s = 500.0
        mesh.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        floor = bpy.data.objects.new("_wondful_clay_floor", mesh)
        if pts:
            # Floor plane perpendicular to the product's up axis, touching its lowest point
            # (a car tilted onto a slope gets a matching sloped floor).
            low = min(pts, key=lambda p: p.dot(up))
            floor.rotation_mode = "QUATERNION"
            floor.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(up)
            floor.location = low
        else:
            floor.location.z = _product_floor_z(collection)
        if ground is not None:
            floor.hide_render = True  # the user's own terrain (ramp, curb, road) is the ground
        mat = bpy.data.materials.new("_wondful_clay_floor_mat")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.62, 0.62, 0.62, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.85
        mesh.materials.append(mat)
        scene.collection.objects.link(floor)
        created += [("obj", floor), ("mesh", mesh), ("mat", mat)]
        sun_data = bpy.data.lights.new("_wondful_clay_sun", type="SUN")
        sun_data.energy = 3.5
        try:
            sun_data.angle = 0.12
        except Exception:
            pass
        sun = bpy.data.objects.new("_wondful_clay_sun", sun_data)
        sun.rotation_euler = (0.85, 0.0, 0.75)
        scene.collection.objects.link(sun)
        created += [("obj", sun), ("light", sun_data)]
        world = bpy.data.worlds.new("_wondful_clay_world")
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0.72, 0.74, 0.76, 1.0)
            bg.inputs[1].default_value = 0.9
        scene.world = world
        created.append(("world", world))
        for k in frame_options:
            setattr(render, k, False)
        if hasattr(render, "film_transparent"):
            render.film_transparent = False
        engine = os.environ.get("WONDFUL_CLAY_ENGINE", "").strip().upper()
        if not engine:
            engine = render.engine if render.engine in {"CYCLES", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"} else "BLENDER_EEVEE_NEXT"
        for candidate in (engine, "BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
            try:
                render.engine = candidate
                break
            except Exception:
                continue
        if render.engine == "CYCLES":
            try:
                scene.cycles.samples = int(os.environ.get("WONDFUL_CLAY_SAMPLES", "48"))
                scene.cycles.use_denoising = os.environ.get("WONDFUL_CLAY_DENOISE", "1") != "0"
            except Exception:
                pass
        render.filepath = filepath
        render.resolution_x, render.resolution_y, render.resolution_percentage = width, height, 100
        _set_png(render.image_settings)
        try:
            render.image_settings.color_mode = "RGB"
        except Exception:
            pass
        bpy.ops.render.render(write_still=True)
        return Path(filepath).exists() and image_dimensions(filepath) == (width, height)
    finally:
        render.engine = snap["engine"]
        render.filepath = snap["filepath"]
        render.resolution_x, render.resolution_y, render.resolution_percentage = snap["x"], snap["y"], snap["pct"]
        _restore_image_format(render.image_settings, snap["fmt"])
        if hasattr(render, "film_transparent"):
            render.film_transparent = snap["film"]
        for k, v in frame_options.items():
            setattr(render, k, v)
        scene.world = snap["world"]
        for kind, block in created:
            try:
                coll = {"obj": bpy.data.objects, "mesh": bpy.data.meshes, "mat": bpy.data.materials,
                        "light": bpy.data.lights, "world": bpy.data.worlds}[kind]
                coll.remove(block)
            except Exception:
                pass
