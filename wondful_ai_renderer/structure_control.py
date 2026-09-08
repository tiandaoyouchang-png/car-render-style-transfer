from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

import bpy
import numpy as np
import mathutils
from bpy_extras.object_utils import world_to_camera_view


WHEEL_KEYWORDS = ("wheel", "tire", "tyre", "rim", "轮", "胎")


def geometry_center_world(obj):
    """A geometry-derived anchor; imported meshes may share the same object origin."""
    corners = [tuple(corner) for corner in obj.bound_box]
    if len(corners) != 8 or all(corner == (-1.0, -1.0, -1.0) for corner in corners):
        raise ValueError("Object has no valid geometry bounds")
    center = mathutils.Vector(tuple(sum(c[i] for c in corners) / 8 for i in range(3)))
    return obj.matrix_world @ center


def resolve_structure_objects(context, props=None) -> tuple[list[bpy.types.Object], str]:
    """Return visible Mesh objects from the user-selected product Collection.

    The Scene Camera remains the whole-frame composition authority. Structure Guide
    and product Mask are generated only from ``props.product_collection``. Objects in
    child Collections are included through ``Collection.all_objects``. No active
    selection, red-material heuristic, or whole-scene fallback is used.
    """
    scene = context.scene
    if not scene.camera:
        return [], "NO_CAMERA"
    collection = getattr(props, "product_collection", None) if props is not None else None
    if collection is None:
        return [], "NO_PRODUCT_COLLECTION"

    objects = []
    seen = set()
    for obj in collection.all_objects:
        if obj.name in seen:
            continue
        seen.add(obj.name)
        if obj.type != "MESH" or getattr(obj, "hide_render", False):
            continue
        # Ignore Collections that are not linked into the current Scene.
        try:
            if scene.objects.get(obj.name) is None:
                continue
        except Exception:
            pass
        try:
            if not obj.visible_get(view_layer=context.view_layer):
                continue
        except Exception:
            pass
        objects.append(obj)
    return objects, "PRODUCT_COLLECTION"


def _object_intersects_camera_frame(scene, camera, obj) -> bool:
    """Cheap frustum screen-overlap test using the evaluated object's bounding box."""
    xs = []
    ys = []
    positive = 0
    try:
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            ndc = world_to_camera_view(scene, camera, world)
            if ndc.z <= 0:
                continue
            positive += 1
            xs.append(float(ndc.x))
            ys.append(float(ndc.y))
    except Exception:
        return True
    if not positive or not xs or not ys:
        return False
    return not (max(xs) < 0.0 or min(xs) > 1.0 or max(ys) < 0.0 or min(ys) > 1.0)


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set((float(x), float(y)) for x, y in points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _fill_polygon_scanline(img: np.ndarray, polygon: list[tuple[float, float]], value) -> None:
    if len(polygon) < 3:
        return
    h, w = img.shape[:2]
    ys = [p[1] for p in polygon]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(h - 1, int(math.ceil(max(ys))))
    n = len(polygon)
    for y in range(y0, y1 + 1):
        scan_y = y + 0.5
        xs = []
        for i in range(n):
            x1, yy1 = polygon[i]
            x2, yy2 = polygon[(i + 1) % n]
            if yy1 == yy2:
                continue
            if (yy1 <= scan_y < yy2) or (yy2 <= scan_y < yy1):
                t = (scan_y - yy1) / (yy2 - yy1)
                xs.append(x1 + (x2 - x1) * t)
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.ceil(xs[i])))
            xb = min(w - 1, int(math.floor(xs[i + 1])))
            if xb >= xa:
                img[y, xa:xb + 1] = value


def _draw_line(img: np.ndarray, a, b, color, width: int = 1) -> None:
    h, w = img.shape[:2]
    x0, y0 = float(a[0]), float(a[1])
    x1, y1 = float(b[0]), float(b[1])
    steps = max(1, int(max(abs(x1 - x0), abs(y1 - y0))))
    xs = np.rint(np.linspace(x0, x1, steps + 1)).astype(np.int32)
    ys = np.rint(np.linspace(y0, y1, steps + 1)).astype(np.int32)
    radius = max(0, int(width) // 2)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            xx = xs + dx
            yy = ys + dy
            valid = (xx >= 0) & (xx < w) & (yy >= 0) & (yy < h)
            img[yy[valid], xx[valid]] = color


def _draw_cross(img: np.ndarray, p, color, radius: int = 8, width: int = 2) -> None:
    x, y = p
    _draw_line(img, (x - radius, y), (x + radius, y), color, width)
    _draw_line(img, (x, y - radius), (x, y + radius), color, width)


def _save_rgba(path: Path, rgba: np.ndarray, name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w, channels = rgba.shape
    if channels != 4:
        raise ValueError("Expected RGBA array")
    image = bpy.data.images.new(name=name, width=w, height=h, alpha=True, float_buffer=False)
    try:
        try:
            image.colorspace_settings.name = "Non-Color"
        except Exception:
            pass
        # Blender image pixels are bottom-up; guide arrays are top-down image coordinates.
        flat = np.ascontiguousarray(rgba[::-1].astype(np.float32)).reshape(-1)
        image.pixels.foreach_set(flat)
        image.filepath_raw = str(path)
        image.file_format = "PNG"
        image.save()
    finally:
        try:
            bpy.data.images.remove(image)
        except Exception:
            pass


def _expand_polygon_from_center(poly: list[tuple[float, float]], width: int, height: int, factor: float = 1.10):
    if not poly:
        return poly
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    result = []
    for x, y in poly:
        nx = cx + (x - cx) * factor
        ny = cy + (y - cy) * factor
        result.append((min(width - 1.0, max(0.0, nx)), min(height - 1.0, max(0.0, ny))))
    return result


def _dilate_binary(mask: np.ndarray, radius: int) -> np.ndarray:
    """Small dependency-free box dilation for edit masks."""
    radius = max(0, int(radius))
    if radius <= 0:
        return mask.astype(bool, copy=True)
    src = mask.astype(bool, copy=False)
    h, w = src.shape
    horiz = src.copy()
    for dx in range(1, radius + 1):
        horiz[:, dx:] |= src[:, :-dx]
        horiz[:, :-dx] |= src[:, dx:]
    out = horiz.copy()
    for dy in range(1, radius + 1):
        out[dy:, :] |= horiz[:-dy, :]
        out[:-dy, :] |= horiz[dy:, :]
    return out


def build_structure_guides(context, props, output_dir: str | Path, width: int, height: int) -> dict:
    """Build product structure guidance from the selected product Collection.

    The active Scene Camera controls the whole-frame composition. Every visible Mesh
    in ``props.product_collection`` (including child Collections) is treated as product
    and projected into ``structure_guide.png`` plus the product Mask. No color heuristic
    and no whole-scene Mesh fallback is used.
    """
    objects, source_mode = resolve_structure_objects(context, props)
    if not objects:
        return {"enabled": False, "source_mode": source_mode, "object_names": []}

    scene = context.scene
    camera = scene.camera
    if not camera:
        return {"enabled": False, "source_mode": source_mode, "object_names": []}

    width = max(64, int(width))
    height = max(64, int(height))
    depsgraph = context.evaluated_depsgraph_get()

    scene_points: list[tuple[float, float]] = []
    scene_edges: list[tuple[tuple[float, float], tuple[float, float]]] = []
    product_points: list[tuple[float, float]] = []
    product_triangles: list[list[tuple[float, float]]] = []
    wheel_points: list[tuple[float, float]] = []
    contributing_names: list[str] = []
    product_names: list[str] = []

    for obj in objects:
        # 2.19: membership in the selected Collection is the product definition.
        is_product = True
        eval_obj = obj.evaluated_get(depsgraph)
        if not _object_intersects_camera_frame(scene, camera, eval_obj):
            continue
        mesh = None
        object_contributed = False
        try:
            mesh = eval_obj.to_mesh()
            coords: list[tuple[float, float] | None] = [None] * len(mesh.vertices)
            for i, vertex in enumerate(mesh.vertices):
                world = eval_obj.matrix_world @ vertex.co
                ndc = world_to_camera_view(scene, camera, world)
                if ndc.z <= 0:
                    continue
                x = float(ndc.x) * width
                y = (1.0 - float(ndc.y)) * height
                # Keep a generous margin so geometry crossing the frame boundary retains edges.
                if -width <= x <= width * 2 and -height <= y <= height * 2:
                    coords[i] = (x, y)
                    clipped = (min(width - 1, max(0.0, x)), min(height - 1, max(0.0, y)))
                    scene_points.append(clipped)
                    if is_product:
                        product_points.append(clipped)
                    object_contributed = True

            if is_product:
                try:
                    mesh.calc_loop_triangles()
                    tri_count = len(mesh.loop_triangles)
                    tri_stride = max(1, int(math.ceil(tri_count / 24000.0)))
                    for tri_index, tri in enumerate(mesh.loop_triangles):
                        if tri_index % tri_stride:
                            continue
                        pts = [coords[i] for i in tri.vertices]
                        if all(p is not None for p in pts):
                            product_triangles.append([p for p in pts if p is not None])
                except Exception:
                    pass

            edge_count = len(mesh.edges)
            stride = max(1, int(math.ceil(edge_count / 9000.0)))
            for edge_index, edge in enumerate(mesh.edges):
                if edge_index % stride:
                    continue
                a = coords[edge.vertices[0]]
                b = coords[edge.vertices[1]]
                if a is not None and b is not None:
                    scene_edges.append((a, b))
        finally:
            if mesh is not None:
                try:
                    eval_obj.to_mesh_clear()
                except Exception:
                    pass

        if object_contributed:
            contributing_names.append(obj.name)
            if is_product:
                product_names.append(obj.name)

        if is_product and any(token in obj.name.lower() for token in WHEEL_KEYWORDS):
            try:
                ndc = world_to_camera_view(scene, camera, geometry_center_world(eval_obj))
                if ndc.z > 0 and 0 <= ndc.x <= 1 and 0 <= ndc.y <= 1:
                    wheel_points.append((float(ndc.x) * width, (1.0 - float(ndc.y)) * height))
            except (ValueError, AttributeError, ReferenceError):
                pass

    if len(scene_points) < 3:
        return {
            "enabled": False,
            "source_mode": source_mode,
            "product_collection_name": getattr(getattr(props, "product_collection", None), "name", ""),
            "object_names": contributing_names,
            "reason": "PRODUCT_COLLECTION_OUTSIDE_CAMERA_OR_EMPTY",
        }

    scene_hull = _convex_hull(scene_points)
    scene_x = [p[0] for p in scene_points]
    scene_y = [p[1] for p in scene_points]
    scene_bbox = (min(scene_x), min(scene_y), max(scene_x), max(scene_y))

    product_available = len(product_points) >= 3
    product_hull = _convex_hull(product_points) if product_available else []
    product_silhouette = np.zeros((height, width), dtype=np.float32)
    if product_available:
        if product_triangles:
            for tri in product_triangles:
                _fill_polygon_scanline(product_silhouette, tri, 1.0)
        else:
            _fill_polygon_scanline(product_silhouette, product_hull, 1.0)
    product_occupied = product_silhouette > 0.5

    if product_available:
        yy, xx = np.nonzero(product_occupied)
        if len(xx) >= 3:
            bbox = (float(xx.min()), float(yy.min()), float(xx.max()), float(yy.max()))
        else:
            xs = [p[0] for p in product_hull]
            ys = [p[1] for p in product_hull]
            bbox = (min(xs), min(ys), max(xs), max(ys))
    else:
        bbox = scene_bbox
    center = ((bbox[0] + bbox[2]) * 0.5, (bbox[1] + bbox[3]) * 0.5)

    # Product Collection guide: only the selected product geometry is structural truth.
    guide = np.zeros((height, width, 4), dtype=np.float32)
    guide[:, :, 3] = 1.0
    if product_available:
        guide[product_occupied] = np.array([0.28, 0.012, 0.012, 1.0], dtype=np.float32)
    for a, b in scene_edges:
        _draw_line(guide, a, b, np.array([0.92, 0.92, 0.92, 1.0], dtype=np.float32), width=1)
    if product_hull:
        for i in range(len(product_hull)):
            _draw_line(guide, product_hull[i], product_hull[(i + 1) % len(product_hull)], np.array([1.0, 0.15, 0.08, 1.0], dtype=np.float32), width=3)
    _draw_cross(guide, center, np.array([0.2, 1.0, 0.35, 1.0], dtype=np.float32), radius=max(8, min(width, height) // 80), width=3)
    for p in wheel_points:
        _draw_cross(guide, p, np.array([0.0, 0.85, 1.0, 1.0], dtype=np.float32), radius=max(7, min(width, height) // 90), width=3)

    out = Path(output_dir)
    guide_path = out / "structure_guide.png"
    _save_rgba(guide_path, guide, "Wondful_ProductCollectionStructureGuide")

    visual_mask_path = ""
    edit_mask_path = ""
    dilation_radius = 0
    mask_source = "NONE"
    if product_available:
        mask_visual = np.zeros((height, width, 4), dtype=np.float32)
        mask_visual[:, :, 3] = 1.0
        mask_visual[product_occupied] = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)
        dilation_radius = max(6, min(width, height) // 80)
        editable = _dilate_binary(product_occupied, dilation_radius)
        edit_mask = np.ones((height, width, 4), dtype=np.float32)
        edit_mask[:, :, :3] = 1.0
        edit_mask[editable, 3] = 0.0
        visual_path = out / "product_structure_mask.png"
        edit_path = out / "product_edit_mask.png"
        _save_rgba(visual_path, mask_visual, "Wondful_StructureMask")
        _save_rgba(edit_path, edit_mask, "Wondful_ProductEditMask")
        visual_mask_path = str(visual_path)
        edit_mask_path = str(edit_path)
        mask_source = "PROJECTED_MESH_TRIANGLES" if product_triangles else "CONVEX_HULL_FALLBACK"

    metadata = {
        "enabled": True,
        "source_mode": source_mode,
        "camera_name": camera.name,
        "product_collection_name": getattr(getattr(props, "product_collection", None), "name", ""),
        "object_names": contributing_names,
        "product_object_names": product_names,
        # Keep the old key for compatibility with older prompt/audit code, but it now
        # means Collection meshes contributing inside the current camera frame.
        "camera_visible_mesh_count": len(contributing_names),
        "product_collection_mesh_count": len(contributing_names),
        "product_mask_available": bool(product_available),
        "scene_bbox_normalized": [
            round(scene_bbox[0] / width, 6), round(scene_bbox[1] / height, 6),
            round(scene_bbox[2] / width, 6), round(scene_bbox[3] / height, 6),
        ],
        "bbox_pixels": [round(v, 2) for v in bbox],
        "bbox_normalized": [round(bbox[0] / width, 6), round(bbox[1] / height, 6), round(bbox[2] / width, 6), round(bbox[3] / height, 6)],
        "center_normalized": [round(center[0] / width, 6), round(center[1] / height, 6)],
        "wheel_points_normalized": [[round(x / width, 6), round(y / height, 6)] for x, y in wheel_points],
        "wheel_anchor_source": "NAMED_MESH_BOUNDING_BOX_CENTER_ESTIMATE",
        "mask_source": mask_source,
        "edit_mask_dilation_px": int(dilation_radius),
        "guide_path": str(guide_path),
        "mask_path": visual_mask_path,
        "edit_mask_path": edit_mask_path,
    }
    (out / "structure_control.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata
