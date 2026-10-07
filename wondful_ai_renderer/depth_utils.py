"""Pure-numpy depth normalization for the structure packet (no bpy)."""
from __future__ import annotations

import math

import numpy as np


def normalize_depth(depth: np.ndarray, valid: np.ndarray, product: np.ndarray | None = None,
                    margin: float = 0.35) -> tuple[np.ndarray, float, float]:
    """Return (depth_norm, near, far) with near=1 (white) and far=0 (black).

    The window is fitted to the *product* pixels when there are any, extended by
    ``margin`` of the product depth range so the floor right around the product
    still reads as a gradient.  Fitting to the whole scene (a 60 m ground plane,
    distant walls) squeezes the product into the top few percent of the range
    and the image model sees a flat white silhouette with no surface relief.
    Pixels outside the window clamp to 0/1; invalid pixels are 0.
    """
    depth = np.asarray(depth, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool)
    out = np.zeros_like(depth, dtype=np.float32)
    if not np.any(valid):
        return out, 0.0, 1.0
    focus = valid & np.asarray(product, dtype=bool) if product is not None else valid
    if np.count_nonzero(focus) < 16:
        focus = valid
    samples = depth[focus]
    near = float(np.percentile(samples, 0.5))
    far = float(np.percentile(samples, 99.5))
    if not math.isfinite(near) or not math.isfinite(far) or far <= near + 1e-8:
        near, far = float(samples.min()), float(samples.max())
    if focus is not valid and far > near:
        far = far + (far - near) * float(margin)
    if far <= near + 1e-8:
        far = near + 1.0
    out[valid] = 1.0 - np.clip((depth[valid] - near) / (far - near), 0.0, 1.0)
    return out, near, far
