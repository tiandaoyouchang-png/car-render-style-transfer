"""Canvas checks and conservative repair planning; no Blender calls in workers."""
import math
import struct
import zlib
from pathlib import Path


# Providers may quantize a requested canvas to a nearby supported ratio. Keep
# small deviations eligible for local aspect-fit postprocessing while retaining
# a stricter exact-ratio flag for diagnostics and repair decisions.
ASPECT_FIT_TOLERANCE = 0.01


def image_dimensions(path):
    """Read common generated-image headers without loading bpy on a worker thread."""
    try:
        with Path(path).open("rb") as f:
            head = f.read(32)
            if head.startswith(b"\x89PNG\r\n\x1a\n") and head[12:16] == b"IHDR":
                return struct.unpack(">II", head[16:24])
            if head[:2] == b"BM" and len(head) >= 26:
                w, h = struct.unpack("<ii", head[18:26])
                return abs(w), abs(h)
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                if head[12:16] == b"VP8X":
                    return 1 + int.from_bytes(head[24:27], "little"), 1 + int.from_bytes(head[27:30], "little")
                if head[12:16] == b"VP8L" and head[20] == 0x2F:
                    bits = int.from_bytes(head[21:25], "little")
                    return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
                if head[12:16] == b"VP8 " and head[23:26] == b"\x9d\x01\x2a":
                    w, h = struct.unpack("<HH", head[26:30])
                    return w & 0x3FFF, h & 0x3FFF
            if head[:2] == b"\xff\xd8":
                f.seek(2)
                while f.tell() < 8 * 1024 * 1024:
                    marker = f.read(1)
                    if not marker:
                        break
                    if marker != b"\xff":
                        continue
                    while marker == b"\xff":
                        marker = f.read(1)
                    if not marker or marker in (b"\xd9", b"\xda"):
                        break
                    if marker == b"\x01" or 0xD0 <= marker[0] <= 0xD8:
                        continue
                    size = struct.unpack(">H", f.read(2))[0]
                    if size < 2:
                        break
                    if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                        _, h, w = struct.unpack(">BHH", f.read(5))
                        return w, h
                    f.seek(size - 2, 1)
    except (OSError, ValueError, IndexError, struct.error):
        pass
    return None


def assess_canvas(actual_size, target_size):
    if not actual_size or min(actual_size) <= 0 or not target_size or min(target_size) <= 0:
        return {"matches": False, "known": False, "message": "无法确认生成图片尺寸，原图已保留。"}
    aw, ah = actual_size
    tw, th = target_size
    error = abs((aw / ah) / (tw / th) - 1.0)
    # Allow integer pixel rounding, but never correct a mismatched frame by cropping.
    matches = error <= max(0.004, 1.0 / aw + 1.0 / ah)
    fit_compatible = error <= max(ASPECT_FIT_TOLERANCE, 1.0 / aw + 1.0 / ah)
    exact_size = aw == tw and ah == th
    if matches:
        message = "" if exact_size else f"生成画布 {aw}×{ah} 将等比适配到白模 {tw}×{th}，未裁切、未拉伸。"
    elif fit_compatible:
        message = f"生成比例 {aw}×{ah} 与白模 {tw}×{th} 略有差异；将等比适配并透明留边，未裁切、未拉伸。"
    else:
        message = f"生成比例 {aw}×{ah} 与白模 {tw}×{th} 不符；已保留完整原图，未裁切。"
    return {"matches": matches, "known": True, "actual_size": [aw, ah],
            "target_size": [tw, th], "relative_aspect_error": error,
            "fit_compatible": fit_compatible, "exact_size": exact_size,
            "message": message}


def valid_bbox(raw):
    if not isinstance(raw, (list, tuple)) or len(raw) != 4:
        return None
    try:
        values = tuple(float(v) for v in raw)
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in values):
        return None
    l, t, r, b = values
    return values if r > l and b > t else None


def bbox_metrics(target, observed):
    target, observed = valid_bbox(target), valid_bbox(observed)
    if target is None or observed is None:
        return None
    l, t, r, b = target
    a, c, d, e = observed
    intersect = max(0, min(r, d) - max(l, a)) * max(0, min(b, e) - max(t, c))
    union = (r-l)*(b-t) + (d-a)*(e-c) - intersect
    return {"bbox_iou": intersect / union,
            "center_dx": (a+d-l-r)/2, "center_dy": (c+e-t-b)/2,
            "width_ratio": (d-a)/(r-l), "height_ratio": (e-c)/(b-t)}


def assess_audit(data, structure, canvas, threshold):
    result = dict(data or {})
    try:
        score = int(float(result.get("overall_score", -1)))
    except (ValueError, TypeError, OverflowError):
        score = -1
    score = max(-1, min(100, score))
    metrics = bbox_metrics(structure.get("bbox_normalized"), result.get("observed_bbox"))
    result["geometry_metrics"] = metrics
    result["geometry_metrics_source"] = "AI_ESTIMATED_BBOX" if metrics else "UNAVAILABLE"
    if metrics:
        drifted = (abs(metrics["center_dx"]) > 0.015 or abs(metrics["center_dy"]) > 0.015
                   or abs(metrics["width_ratio"]-1) > 0.04 or abs(metrics["height_ratio"]-1) > 0.04
                   or metrics["bbox_iou"] < 0.9)
        if drifted:
            score = min(score, 79, threshold - 1)
            result["correction"] = (
                f"按白模恢复主体：中心需水平修正 {-metrics['center_dx']*100:.2f}% 画宽、"
                f"垂直修正 {-metrics['center_dy']*100:.2f}% 画高；"
                f"当前宽度为目标的 {metrics['width_ratio']*100:.1f}%，"
                f"高度为目标的 {metrics['height_ratio']*100:.1f}%。"
            ) + str(result.get("correction") or "")
    # A model's explicit failure cannot be erased by its contradictory high score.
    if result.get("passed") is False:
        score = min(score, threshold - 1)
    if not (canvas.get("matches") or canvas.get("fit_compatible")):
        score = 0
        result["correction"] = canvas["message"] + "下一轮回到原始白模整幅画布生成，保持相同宽高比。"
    result["overall_score"] = score
    result["passed"] = score >= threshold and bool(canvas.get("matches") or canvas.get("fit_compatible"))
    result["canvas"] = canvas
    return result


def repair_region(structure, audit, actual_size, camera_size, threshold):
    """Unknown or perspective-changing repairs restart from the original white model."""
    canvas = assess_canvas(actual_size, camera_size)
    if not (canvas["matches"] or canvas.get("fit_compatible")):
        return None
    target, observed = valid_bbox(structure.get("bbox_normalized")), valid_bbox((audit or {}).get("observed_bbox"))
    try:
        confidence = float((audit or {}).get("bbox_confidence", 0))
        viewpoint = float((audit or {}).get("viewpoint", 0))
    except (TypeError, ValueError):
        return None
    if target is None or observed is None or not (0.7 <= confidence <= 1 and threshold <= viewpoint <= 100):
        return None
    pad = 0.02
    region = (max(0, min(target[0], observed[0])-pad), max(0, min(target[1], observed[1])-pad),
              min(1, max(target[2], observed[2])+pad), min(1, max(target[3], observed[3])+pad))
    # A near-full-frame mask provides little benefit; use the authoritative base.
    return region if (region[2]-region[0])*(region[3]-region[1]) < 0.8 else None


def write_repair_mask(path, size, region):
    """RGBA PNG with a transparent union of observed and desired product extents."""
    width, height = map(int, size)
    region = valid_bbox(region)
    if width < 1 or height < 1 or region is None:
        raise ValueError("Invalid repair canvas or region")
    x0, y0 = int(math.floor(region[0]*width)), int(math.floor(region[1]*height))
    x1, y1 = int(math.ceil(region[2]*width)), int(math.ceil(region[3]*height))
    full = b"\xff\xff\xff\xff" * width
    editable = full[:x0*4] + b"\xff\xff\xff\x00" * (x1-x0) + full[x1*4:]
    compressor = zlib.compressobj()
    chunks = [compressor.compress(b"\x00" + (editable if y0 <= y < y1 else full)) for y in range(height)]
    compressed = b"".join(chunks) + compressor.flush()
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind+content) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", compressed) + chunk(b"IEND", b""))
    Path(path).write_bytes(data)
    return str(path)


def canvas_contract(width, height, target_size=""):
    return (
        f"【生成画布】白模完整画布为 {int(width)}×{int(height)}，宽高比 {width/height:.8f}。"
        + (f"建议输出尺寸 {target_size}，须维持同一宽高比。" if target_size else "")
        + "将 Camera Base 作为整幅图像的编辑底图，所有结构图与其逐像素坐标对应。"
          "调用图像工具时，如有原图保真度参数，选择最高保真；如有尺寸或比例参数，传入与白模相同的比例。"
          "不得先生成其他比例再居中裁切、拉伸、加边框或把白模缩进另一张画布。"
    )
