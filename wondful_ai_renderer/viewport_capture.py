from __future__ import annotations

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


def _capture_opengl_view(context, window, area, region, filepath: str) -> bool:
    """Legacy active-view capture retained as a fallback utility."""
    scene = context.scene
    render = scene.render
    old_path = render.filepath
    old_x, old_y, old_pct = render.resolution_x, render.resolution_y, render.resolution_percentage
    old_format = render.image_settings.file_format
    try:
        render.filepath = filepath
        render.resolution_x = max(1, int(region.width))
        render.resolution_y = max(1, int(region.height))
        render.resolution_percentage = 100
        render.image_settings.file_format = "PNG"
        with context.temp_override(window=window, area=area, region=region, scene=scene):
            result = bpy.ops.render.opengl(animation=False, sequencer=False, write_still=True, view_context=True)
        return "FINISHED" in result and Path(filepath).exists()
    finally:
        render.filepath = old_path
        render.resolution_x, render.resolution_y = old_x, old_y
        render.resolution_percentage = old_pct
        render.image_settings.file_format = old_format


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
    old_format = render.image_settings.file_format
    old_color_mode = getattr(render.image_settings, "color_mode", None)
    frame_options = {key: getattr(render, key) for key in ("use_border", "use_crop_to_border", "use_compositing", "use_sequencer", "use_multiview") if hasattr(render, key)}
    try:
        for key in frame_options:
            setattr(render, key, False)
        render.filepath = filepath
        render.resolution_x = width
        render.resolution_y = height
        render.resolution_percentage = 100
        render.image_settings.file_format = "PNG"
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
        render.image_settings.file_format = old_format
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
