from __future__ import annotations

import numpy as np


def preview_dimensions(width: int, height: int, max_edge: int = 1400) -> tuple[int, int]:
    width = max(1, int(width))
    height = max(1, int(height))
    max_edge = max(256, int(max_edge))
    scale = min(1.0, max_edge / float(max(width, height)))
    return max(1, int(round(width * scale))), max(1, int(round(height * scale)))


def resize_rgba_nearest(rgba: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """Resize an HxWx4 float array with deterministic nearest-neighbour sampling."""
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError("rgba must be HxWx4")
    src_h, src_w = int(rgba.shape[0]), int(rgba.shape[1])
    target_w = max(1, int(target_w))
    target_h = max(1, int(target_h))
    if src_w == target_w and src_h == target_h:
        return rgba.astype(np.float32, copy=True)
    xs = np.minimum(((np.arange(target_w) + 0.5) * src_w / target_w).astype(np.intp), src_w - 1)
    ys = np.minimum(((np.arange(target_h) + 0.5) * src_h / target_h).astype(np.intp), src_h - 1)
    return rgba[ys[:, None], xs[None, :], :].astype(np.float32, copy=False)


def compose_split(reference: np.ndarray, result: np.ndarray, factor: float, divider_px: int = 4) -> np.ndarray:
    if reference.shape != result.shape:
        raise ValueError("reference and result must have identical shapes")
    factor = max(0.0, min(1.0, float(factor)))
    h, w, _ = reference.shape
    split = int(round(w * factor))
    out = result.astype(np.float32, copy=True)
    if split > 0:
        out[:, :split, :] = reference[:, :split, :]
    if 0 < split < w and divider_px > 0:
        half = max(1, int(divider_px))
        x0 = max(0, split - half)
        x1 = min(w, split + half)
        out[:, x0:x1, :3] = 1.0
        out[:, x0:x1, 3] = 1.0
    return out


def compose_overlay(reference: np.ndarray, result: np.ndarray, ai_opacity: float) -> np.ndarray:
    if reference.shape != result.shape:
        raise ValueError("reference and result must have identical shapes")
    alpha = max(0.0, min(1.0, float(ai_opacity)))
    out = reference.astype(np.float32, copy=True)
    out[:, :, :3] = reference[:, :, :3] * (1.0 - alpha) + result[:, :, :3] * alpha
    out[:, :, 3] = 1.0
    return out


def compose_difference(reference: np.ndarray, result: np.ndarray, gain: float = 2.0) -> np.ndarray:
    if reference.shape != result.shape:
        raise ValueError("reference and result must have identical shapes")
    out = np.empty_like(reference, dtype=np.float32)
    out[:, :, :3] = np.clip(np.abs(reference[:, :, :3] - result[:, :, :3]) * float(gain), 0.0, 1.0)
    out[:, :, 3] = 1.0
    return out


def compose_outline(result: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Show the authoritative product silhouette without interpreting lighting as drift."""
    if result.shape != mask.shape:
        raise ValueError("result and mask must have identical shapes")
    foreground = mask[:, :, 0] > 0.5
    padded = np.pad(foreground, 1, constant_values=False)
    interior = (foreground & padded[:-2, 1:-1] & padded[2:, 1:-1]
                & padded[1:-1, :-2] & padded[1:-1, 2:])
    edge = foreground & ~interior
    # Two preview pixels remain visible on a large render.
    p = np.pad(edge, 1, constant_values=False)
    edge = edge | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    out = result.astype(np.float32, copy=True)
    out[edge] = (0.0, 1.0, 1.0, 1.0)
    return out
