"""Identity-preservation helpers for Wondful 3.1.5.

The worker-safe path builds a spatial keep-mask from Blender's Object Index map
and Jev semantic results. Optional hard pixel restore is main-thread only and is
explicitly opt-in because Camera Base may be a white/solid viewport capture.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path
from typing import Any

import numpy as np


def _dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    radius = max(0, int(radius))
    src = np.asarray(mask, dtype=bool)
    if radius <= 0:
        return src.copy()
    h, w = src.shape
    out = src.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            y0 = max(0, dy)
            y1 = min(h, h + dy)
            x0 = max(0, dx)
            x1 = min(w, w + dx)
            sy0 = max(0, -dy)
            sy1 = sy0 + (y1 - y0)
            sx0 = max(0, -dx)
            sx1 = sx0 + (x1 - x0)
            if y1 > y0 and x1 > x0:
                out[y0:y1, x0:x1] |= src[sy0:sy1, sx0:sx1]
    return out


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_gray_png(path: str | Path, gray: np.ndarray) -> str:
    """Write an 8-bit grayscale PNG without bpy/Pillow; safe on a worker thread."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(gray, dtype=np.uint8)
    if arr.ndim != 2:
        raise ValueError("Expected a 2D grayscale array")
    h, w = arr.shape
    raw = b"".join(b"\x00" + np.ascontiguousarray(arr[y]).tobytes() for y in range(h))
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )
    target.write_bytes(data)
    return str(target)


def build_identity_preserve_mask(
    part_index_path: str | Path,
    semantic_results: list[dict[str, Any]],
    output_path: str | Path,
    *,
    padding_px: int = 2,
) -> dict[str, Any]:
    """Create white=preserve identity mask from Jev-confirmed Object Index IDs."""
    source = Path(part_index_path)
    if not source.is_file():
        return {"enabled": False, "reason": "PART_INDEX_UNAVAILABLE", "path": ""}

    selected = []
    for row in semantic_results or []:
        if not row.get("identity_critical"):
            continue
        index = row.get("part_id_index")
        try:
            index = int(index)
        except (TypeError, ValueError):
            continue
        if index > 0:
            selected.append((index, str(row.get("part_class", "OTHER"))))

    if not selected:
        return {"enabled": False, "reason": "NO_IDENTITY_PARTS", "path": ""}

    index_map = np.load(str(source), allow_pickle=False)
    if index_map.ndim != 2:
        raise ValueError("Part index map must be 2D")
    ids = np.array(sorted({index for index, _role in selected}), dtype=index_map.dtype)
    mask = np.isin(index_map, ids)
    raw_pixels = int(mask.sum())
    if raw_pixels <= 0:
        return {
            "enabled": False,
            "reason": "IDENTITY_PARTS_NOT_VISIBLE",
            "path": "",
            "indices": [int(x) for x in ids],
        }

    mask = _dilate(mask, padding_px)
    gray = np.where(mask, 255, 0).astype(np.uint8)
    target = write_gray_png(output_path, gray)
    yy, xx = np.nonzero(mask)
    h, w = mask.shape
    return {
        "enabled": True,
        "path": target,
        "indices": [int(x) for x in ids],
        "roles": sorted({role for _index, role in selected}),
        "padding_px": int(padding_px),
        "raw_pixel_count": raw_pixels,
        "pixel_count": int(mask.sum()),
        "coverage": float(mask.mean()),
        "bbox_normalized": [
            round(float(xx.min()) / w, 6),
            round(float(yy.min()) / h, 6),
            round(float(xx.max() + 1) / w, 6),
            round(float(yy.max() + 1) / h, 6),
        ],
    }


def _load_bpy_rgba(path: str | Path, *, non_color: bool = False):
    import bpy

    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        if non_color:
            try:
                image.colorspace_settings.name = "Non-Color"
            except Exception:
                pass
        w, h = map(int, image.size)
        pixels = np.empty(w * h * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        rgba = pixels.reshape(h, w, 4)[::-1].copy()
        return rgba
    finally:
        try:
            bpy.data.images.remove(image)
        except Exception:
            pass


def hard_restore_identity_pixels(
    final_path: str | Path,
    source_path: str | Path,
    mask_path: str | Path,
    output_path: str | Path,
) -> str:
    """Main-thread-only exact pixel restore using Camera Base as source.

    This is intentionally opt-in. If Camera Base is a white/solid viewport,
    users should keep MASK mode instead of HARD_RESTORE.
    """
    import bpy

    final = _load_bpy_rgba(final_path, non_color=False)
    source = _load_bpy_rgba(source_path, non_color=False)
    mask_rgba = _load_bpy_rgba(mask_path, non_color=True)
    if final.shape != source.shape or final.shape[:2] != mask_rgba.shape[:2]:
        raise ValueError(
            f"Identity restore canvas mismatch: final={final.shape[:2]} source={source.shape[:2]} mask={mask_rgba.shape[:2]}"
        )

    alpha = np.clip(mask_rgba[:, :, 0:1], 0.0, 1.0)
    restored = final.copy()
    restored[:, :, :3] = final[:, :, :3] * (1.0 - alpha) + source[:, :, :3] * alpha

    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    h, w = restored.shape[:2]
    image = bpy.data.images.new(
        name="Wondful_IdentityRestore",
        width=w,
        height=h,
        alpha=True,
        float_buffer=False,
    )
    try:
        try:
            image.colorspace_settings.name = "sRGB"
        except Exception:
            pass
        flat = np.ascontiguousarray(restored[::-1].astype(np.float32)).reshape(-1)
        image.pixels.foreach_set(flat)
        image.filepath_raw = str(target)
        image.file_format = "PNG"
        image.save()
    finally:
        try:
            bpy.data.images.remove(image)
        except Exception:
            pass
    return str(target)
