"""Jev semantic layer for Wondful AI Renderer 3.1.3.

Blender owns deterministic geometry. Jev is used only for semantic judgments.
This module calls the official TypeSafe HTTP API with Python stdlib only, so the
Blender addon does not require typesafe-sdk at runtime. If Jev is unavailable,
local deterministic heuristics are used as a transparent fallback.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest


API_KEY_ENV = "TYPESAFE_API_KEY"
BASE_URL_ENV = "TYPESAFE_BASE_URL"
MODEL_ENV = "TYPESAFE_DEFAULT_MODEL"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
SYSTEM_ONE_PATH = "/v1/systemone"
REFERENCE_CONFIDENCE_THRESHOLD = 0.62
SEMANTIC_CONFIDENCE_THRESHOLD = 0.58

PART_CLASSES = {
    "BODY_PANEL": "car body panel or exterior painted structural surface",
    "GLASS": "window, windshield, fixed transparent glass",
    "TIRE": "rubber tire",
    "WHEEL": "wheel or rim, excluding tire",
    "BRAKE": "brake disc, rotor or caliper",
    "HEADLAMP": "front lamp or headlamp assembly",
    "TAILLAMP": "rear lamp or taillamp assembly",
    "MIRROR": "mirror glass or mirror assembly",
    "LOGO_BADGE": "brand logo, emblem or graphic badge",
    "TEXT_BADGE": "brand wordmark, model lettering or readable badge text",
    "CHROME_TRIM": "bright metallic or chrome trim",
    "BLACK_PLASTIC": "black exterior engineering plastic",
    "INTERIOR": "seat, dashboard, console, steering wheel or interior trim",
    "SCREEN_UI": "display, HUD or cluster with readable UI",
    "SENSOR": "radar, camera, lidar or sensor window",
    "PLATE": "license plate and readable plate characters",
    "OTHER": "none of the above with enough evidence",
}

MATERIAL_CLASSES = {
    "PAINT": "automotive paint with clearcoat",
    "GLASS": "transparent or translucent glass",
    "RUBBER": "tire or sealing rubber",
    "METAL": "bare, brushed or machined metal",
    "CHROME": "high-reflective chrome or mirror metal",
    "BLACK_PLASTIC": "black engineering plastic",
    "GLOSSY_PLASTIC": "glossy or piano-black plastic",
    "MATTE_PLASTIC": "matte or textured plastic",
    "INTERIOR_SOFT": "leather, fabric or soft interior material",
    "EMISSIVE": "emissive LED, light strip or display emission",
    "OPTICAL": "lamp lens or optical transparent component",
    "MIRROR": "mirror reflective material",
    "OTHER": "none of the above with enough evidence",
}

REFERENCE_ROLES = {
    "PRODUCT": "product identity and shape only",
    "STYLE": "environment, lighting, color mood, material rendering and photography",
    "PERSON": "person identity, face, clothing or character",
    "MIXED": "multiple responsibilities are equally important",
    "UNSURE": "not enough evidence to classify safely",
}

THEMES = {
    "COMMERCIAL_STUDIO": "clean premium commercial studio lighting",
    "CINEMATIC_DRAMATIC": "cinematic dramatic light and shadow",
    "MINIMALIST_INDUSTRIAL": "minimal industrial design language",
    "CYBER_TECH": "futuristic technology atmosphere",
    "NATURAL_LIFESTYLE": "natural realistic lifestyle environment",
}

CONTRAST_LEVELS = [
    "very soft diffuse light and very low contrast",
    "soft commercial lighting with gentle shadows",
    "balanced commercial contrast with preserved shadow detail",
    "strong side or rim light with deep shadows",
    "extreme dramatic contrast with sharp highlights and near-black shadows",
]
GLOSS_LEVELS = [
    "fully matte diffuse appearance",
    "fine matte engineering material",
    "semi-gloss material with broad soft highlights",
    "high-gloss polished or piano-black reflections",
    "mirror or chrome-like high reflection",
]
DETAIL_LEVELS = [
    "abstract geometric detail",
    "minimal clean surface detail",
    "standard product assembly detail",
    "premium commercial micro-detail and seams",
    "extremely dense industrial micro-detail",
]

_CACHE_LOCK = threading.RLock()
_CACHE: dict[str, dict[str, Any]] = {}


class JevError(RuntimeError):
    pass


def _key() -> str:
    return os.environ.get(API_KEY_ENV, "").strip()


def backend_status() -> dict[str, Any]:
    configured = bool(_key())
    model = os.environ.get(MODEL_ENV, DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return {
        "mode": "JEV" if configured else "LOCAL_FALLBACK",
        "configured": configured,
        "model": model,
        "message": f"Jev ready · {model}" if configured else f"{API_KEY_ENV} not set · local fallback",
    }


def _system_one(state: Any, questions: dict[str, Any], timeout: float = 10.0) -> dict[str, Any]:
    key = _key()
    if not key:
        raise JevError(f"{API_KEY_ENV} is not configured")
    base = (os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL).rstrip("/")
    model = os.environ.get(MODEL_ENV, DEFAULT_MODEL).strip() or DEFAULT_MODEL
    body = json.dumps(
        {"state": state, "model": model, "questions": questions},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    req = urlrequest.Request(
        base + SYSTEM_ONE_PATH,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "wondful-ai-renderer/3.1.3",
        },
    )
    last = ""
    for attempt in range(2):
        try:
            with urlrequest.urlopen(req, timeout=max(1.0, float(timeout))) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
                raise JevError("Invalid TypeSafe response")
            return data
        except urlerror.HTTPError as exc:
            try:
                detail = exc.read(500).decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            last = f"HTTP {exc.code}: {detail or exc.reason}"
            if exc.code not in {429, 500, 502, 503, 504} or attempt:
                break
            time.sleep(0.35)
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
            if attempt:
                break
            time.sleep(0.2)
    raise JevError(last or "TypeSafe request failed")


def _choice(answer: dict[str, Any]) -> dict[str, Any]:
    probs = answer.get("probabilities") if isinstance(answer, dict) else {}
    probs = probs if isinstance(probs, dict) else {}
    choice = str(answer.get("choice", "")) if isinstance(answer, dict) else ""
    try:
        confidence = float(answer.get("confidence", probs.get(choice, 0.0)))
    except Exception:
        confidence = 0.0
    return {
        "choice": choice,
        "confidence": max(0.0, min(1.0, confidence)),
        "probabilities": {str(k): float(v) for k, v in probs.items() if isinstance(v, (int, float))},
    }


def _noul(answer: dict[str, Any]) -> float:
    try:
        return max(0.0, min(1.0, float(answer.get("noul", 0.5))))
    except Exception:
        return 0.5


def _score(answer: dict[str, Any], descriptions: list[str]) -> dict[str, Any]:
    try:
        raw = float(answer.get("score", 0.0))
    except Exception:
        raw = 0.0
    level = max(1, min(len(descriptions), int(round(raw)) + 1))
    return {"level": level, "score": raw + 1.0, "description": descriptions[level - 1]}


def classify_reference_intent(filepath: str, instruction: str = "", current_kind: str = "") -> dict[str, Any]:
    state = {
        "filename": Path(filepath).name,
        "instruction": instruction or "",
        "current_category": current_kind or "",
    }
    if _key():
        try:
            data = _system_one(
                state,
                {
                    "role": {
                        "type": "choice",
                        "instructions": (
                            "Classify the intended role of this reference in a rendering workflow. "
                            "Choose a single category only when evidence is clear. Use MIXED when multiple "
                            "roles are equally important and UNSURE when evidence is insufficient."
                        ),
                        "criteria": REFERENCE_ROLES,
                    }
                },
            )
            result = _choice(data["answers"].get("role", {}))
            result.update({"backend": "JEV", "model": data.get("model", DEFAULT_MODEL), "error": ""})
            return result
        except Exception as exc:
            error_text = str(exc)
    else:
        error_text = ""

    text = f"{Path(filepath).stem} {instruction}".lower()
    groups = {
        "PRODUCT": ("product", "part", "body", "wheel", "lamp", "造型", "车身", "轮毂", "产品"),
        "STYLE": ("style", "light", "environment", "studio", "风格", "灯光", "环境", "材质", "摄影"),
        "PERSON": ("person", "human", "face", "portrait", "character", "人物", "人脸", "服装"),
    }
    hits = {name: sum(1 for word in words if word in text) for name, words in groups.items()}
    ranked = sorted(hits.items(), key=lambda item: item[1], reverse=True)
    if ranked[0][1] == 0:
        choice = current_kind if current_kind in groups else "UNSURE"
        confidence = 0.34 if choice != "UNSURE" else 0.25
    elif ranked[1][1] > 0 and ranked[0][1] <= ranked[1][1] + 1:
        choice, confidence = "MIXED", 0.55
    else:
        choice = ranked[0][0]
        confidence = min(0.95, 0.55 + 0.12 * ranked[0][1])
    return {"choice": choice, "confidence": confidence, "probabilities": {}, "backend": "LOCAL_FALLBACK", "error": error_text}


def classify_references_batch(items: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Classify multiple reference roles in one System One request.

    Each item requires filepath/instruction/current_kind. Low-confidence policy is
    intentionally left to the caller so the UI can preserve existing categories.
    """
    if not items:
        return []
    if _key():
        state = {
            "references": [
                {
                    "filename": Path(item.get("filepath", "")).name,
                    "instruction": item.get("instruction", ""),
                    "current_category": item.get("current_kind", ""),
                }
                for item in items
            ]
        }
        questions = {}
        for index in range(len(items)):
            questions[f"role_{index}"] = {
                "type": "choice",
                "instructions": (
                    f"Classify references[{index}] by intended rendering responsibility. "
                    "Choose PRODUCT/STYLE/PERSON only with clear evidence; use MIXED for "
                    "multiple equal roles and UNSURE for insufficient evidence."
                ),
                "criteria": REFERENCE_ROLES,
            }
        try:
            data = _system_one(state, questions, timeout=12.0)
            answers = data["answers"]
            output = []
            for index in range(len(items)):
                row = _choice(answers.get(f"role_{index}", {}))
                row.update({"backend": "JEV", "model": data.get("model", DEFAULT_MODEL), "error": ""})
                output.append(row)
            return output
        except Exception as exc:
            error_text = str(exc)
    else:
        error_text = ""

    output = []
    for item in items:
        row = classify_reference_intent(
            item.get("filepath", ""),
            item.get("instruction", ""),
            item.get("current_kind", ""),
        )
        if error_text and not row.get("error"):
            row["error"] = error_text
        output.append(row)
    return output


def analyze_appearance(brief: str, style_notes: list[str] | None = None) -> dict[str, Any]:
    state = {
        "creative_brief": brief or "",
        "style_notes": list(style_notes or []),
        "workflow_rule": "Blender owns camera, composition and geometry unless the user explicitly asks to change them.",
    }
    questions = {
        "theme": {"type": "choice", "instructions": "Choose the primary visual theme.", "criteria": THEMES},
        "contrast": {"type": "score", "instructions": "Judge target lighting contrast.", "criteria": CONTRAST_LEVELS},
        "gloss": {"type": "score", "instructions": "Judge overall material gloss. Do not let one glass or chrome part dominate the whole product.", "criteria": GLOSS_LEVELS},
        "detail": {"type": "score", "instructions": "Judge target surface and industrial detail density.", "criteria": DETAIL_LEVELS},
        "scope": {
            "type": "choice",
            "instructions": "Determine what the user actually wants changed. Respect explicit keep/unchanged constraints.",
            "criteria": {
                "MATERIAL_ONLY": "materials or paint only",
                "LIGHTING_ONLY": "lighting only",
                "ENVIRONMENT_ONLY": "environment, weather or background only",
                "COLOR_ONLY": "color only",
                "FULL_APPEARANCE": "materials, lighting and environment may change, but not Blender geometry/camera",
                "GEOMETRY_REQUEST": "explicit geometry or shape change",
                "COMPOSITION_REQUEST": "explicit camera, framing, scale or position change",
                "AMBIGUOUS": "insufficient evidence",
            },
        },
        "preserve_identity": {
            "type": "noul",
            "instructions": "Should brand logos, wordmarks, model text, plate characters and readable screen text be strictly preserved?",
            "criteria": {"true": "preserve exact identity assets", "false": "user explicitly wants them changed"},
        },
        "structural_change": {
            "type": "noul",
            "instructions": "Did the user explicitly request a change to Blender geometry, camera, framing, position, scale or structure?",
            "criteria": {"true": "explicit structural change requested", "false": "no structural change requested"},
        },
    }
    if _key():
        try:
            data = _system_one(state, questions)
            answers = data["answers"]
            result = {
                "theme": _choice(answers.get("theme", {})),
                "lighting_contrast": _score(answers.get("contrast", {}), CONTRAST_LEVELS),
                "material_gloss": _score(answers.get("gloss", {}), GLOSS_LEVELS),
                "detail_density": _score(answers.get("detail", {}), DETAIL_LEVELS),
                "change_scope": _choice(answers.get("scope", {})),
                "preserve_identity_probability": _noul(answers.get("preserve_identity", {})),
                "structural_change_probability": _noul(answers.get("structural_change", {})),
                "backend": "JEV",
                "model": data.get("model", DEFAULT_MODEL),
                "usage": data.get("usage", {}),
                "error": "",
            }
            result["synthesized"] = _appearance_text(result)
            return result
        except Exception as exc:
            error_text = str(exc)
    else:
        error_text = ""

    text = f"{brief} {' '.join(style_notes or [])}".lower()
    theme = "COMMERCIAL_STUDIO"
    for candidate, words in {
        "CINEMATIC_DRAMATIC": ("电影", "戏剧", "cinematic", "dramatic"),
        "MINIMALIST_INDUSTRIAL": ("极简", "工业", "minimal", "industrial"),
        "CYBER_TECH": ("赛博", "未来", "科技", "cyber", "future"),
        "NATURAL_LIFESTYLE": ("自然", "户外", "生活", "outdoor", "sunlight"),
    }.items():
        if any(word in text for word in words):
            theme = candidate
            break
    contrast = 4 if any(word in text for word in ("高反差", "戏剧", "dramatic")) else 2 if any(word in text for word in ("柔和", "漫射", "soft")) else 3
    gloss = 5 if any(word in text for word in ("镜面", "镀铬", "chrome")) else 4 if any(word in text for word in ("高光", "gloss")) else 2 if any(word in text for word in ("哑光", "matte")) else 3
    detail = 5 if any(word in text for word in ("精密", "微观", "detailed")) else 2 if any(word in text for word in ("极简", "minimal")) else 4
    scope = "FULL_APPEARANCE"
    if any(word in text for word in ("只改材质", "仅改材质", "material only")):
        scope = "MATERIAL_ONLY"
    elif any(word in text for word in ("只改灯光", "仅改灯光", "lighting only")):
        scope = "LIGHTING_ONLY"
    elif any(word in text for word in ("只换环境", "换背景", "environment only")):
        scope = "ENVIRONMENT_ONLY"
    result = {
        "theme": {"choice": theme, "confidence": 0.6},
        "lighting_contrast": {"level": contrast, "score": float(contrast), "description": CONTRAST_LEVELS[contrast - 1]},
        "material_gloss": {"level": gloss, "score": float(gloss), "description": GLOSS_LEVELS[gloss - 1]},
        "detail_density": {"level": detail, "score": float(detail), "description": DETAIL_LEVELS[detail - 1]},
        "change_scope": {"choice": scope, "confidence": 0.6},
        "preserve_identity_probability": 0.92,
        "structural_change_probability": 0.12,
        "backend": "LOCAL_FALLBACK",
        "error": error_text,
    }
    result["synthesized"] = _appearance_text(result)
    return result


def _appearance_text(result: dict[str, Any]) -> str:
    theme = result["theme"].get("choice", "COMMERCIAL_STUDIO")
    scope = result["change_scope"].get("choice", "FULL_APPEARANCE")
    preserve = float(result.get("preserve_identity_probability", 0.0)) >= 0.5
    return (
        f"视觉主题：{THEMES.get(theme, theme)}。"
        f"光照：{result['lighting_contrast']['description']}。"
        f"材质高光：{result['material_gloss']['description']}。"
        f"细节：{result['detail_density']['description']}。"
        f"本轮修改范围：{scope}。"
        + ("车标、字标、车型文字、车牌和屏幕可读文字属于身份关键资产，必须保持原始形状、字形、位置和比例，不得臆造。" if preserve else "")
    )


def _scalar(node: Any, *names: str) -> float | None:
    try:
        for name in names:
            socket = node.inputs.get(name)
            if socket is not None and isinstance(socket.default_value, (int, float)):
                return float(socket.default_value)
    except Exception:
        pass
    return None


def _material_state(material: Any) -> dict[str, Any]:
    result = {"name": getattr(material, "name", "")}
    try:
        tree = material.node_tree if material.use_nodes else None
        bsdf = next((node for node in tree.nodes if getattr(node, "type", "") == "BSDF_PRINCIPLED"), None) if tree else None
        if bsdf:
            values = {
                "metallic": _scalar(bsdf, "Metallic"),
                "roughness": _scalar(bsdf, "Roughness"),
                "ior": _scalar(bsdf, "IOR"),
                "transmission": _scalar(bsdf, "Transmission Weight", "Transmission"),
                "alpha": _scalar(bsdf, "Alpha"),
                "emission_strength": _scalar(bsdf, "Emission Strength"),
            }
            result.update({key: round(value, 4) for key, value in values.items() if value is not None})
    except Exception:
        pass
    return result


def collect_product_object_states(context: Any, props: Any, part_manifest: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    collection = getattr(props, "product_collection", None)
    if collection is None:
        return []
    manifest = part_manifest or {}
    names = set(manifest)
    rows = []
    for obj in collection.all_objects:
        if getattr(obj, "type", "") != "MESH" or getattr(obj, "hide_render", False):
            continue
        if names and obj.name not in names:
            continue
        try:
            if context.scene.objects.get(obj.name) is None:
                continue
        except Exception:
            pass
        try:
            location = [round(float(v), 4) for v in obj.matrix_world.translation]
            dimensions = [round(abs(float(v)), 4) for v in obj.dimensions]
        except Exception:
            location, dimensions = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        materials = []
        try:
            for slot in list(obj.material_slots)[:4]:
                if slot.material is not None:
                    materials.append(_material_state(slot.material))
        except Exception:
            pass
        try:
            vertex_count = len(obj.data.vertices)
            polygon_count = len(obj.data.polygons)
        except Exception:
            vertex_count = polygon_count = 0
        item = {
            "object_name": obj.name,
            "parent_name": getattr(getattr(obj, "parent", None), "name", ""),
            "children": [child.name for child in list(getattr(obj, "children", []))[:8]],
            "collections": [group.name for group in list(getattr(obj, "users_collection", []))[:6]],
            "location_world": location,
            "dimensions": dimensions,
            "vertex_count": int(vertex_count),
            "polygon_count": int(polygon_count),
            "materials": materials,
        }
        if obj.name in manifest:
            item["part_id_rgb"] = manifest[obj.name].get("rgb", [])
            item["part_id_index"] = manifest[obj.name].get("index")
        rows.append(item)
    return rows


def _object_text(state: dict[str, Any]) -> str:
    material_names = " ".join(str(material.get("name", "")) for material in state.get("materials", []))
    return " ".join(
        [str(state.get("object_name", "")), str(state.get("parent_name", "")), material_names]
        + [str(value) for value in state.get("collections", [])]
    ).lower()


def _local_object_semantics(state: dict[str, Any], error_text: str = "") -> dict[str, Any]:
    text = _object_text(state)
    part, part_confidence, critical = "OTHER", 0.45, 0.08
    rules = [
        (("logo", "badge", "emblem", "车标", "徽标"), "LOGO_BADGE", 0.98, 0.99),
        (("wordmark", "nameplate", "letter", "modelname", "字标", "铭牌"), "TEXT_BADGE", 0.96, 0.98),
        (("license", "numberplate", "plate", "车牌"), "PLATE", 0.98, 0.98),
        (("tire", "tyre", "轮胎"), "TIRE", 0.98, 0.05),
        (("wheel", "rim", "轮毂"), "WHEEL", 0.96, 0.05),
        (("brake", "caliper", "rotor", "disc", "制动", "刹车"), "BRAKE", 0.95, 0.05),
        (("headlamp", "headlight", "frontlamp", "前灯", "大灯"), "HEADLAMP", 0.96, 0.1),
        (("taillamp", "taillight", "rearlamp", "尾灯", "后灯"), "TAILLAMP", 0.96, 0.1),
        (("mirror", "后视镜"), "MIRROR", 0.94, 0.08),
        (("windshield", "windscreen", "window", "glass", "风挡", "车窗"), "GLASS", 0.93, 0.05),
        (("screen", "display", "cluster", "infotainment", "hud", "屏幕", "仪表"), "SCREEN_UI", 0.91, 0.9),
        (("sensor", "radar", "lidar", "camera", "雷达", "传感器"), "SENSOR", 0.9, 0.08),
        (("seat", "steering", "dashboard", "console", "interior", "座椅", "内饰", "方向盘"), "INTERIOR", 0.86, 0.05),
        (("chrome", "bright_trim", "molding", "镀铬"), "CHROME_TRIM", 0.84, 0.05),
        (("black_plastic", "abs", "塑料"), "BLACK_PLASTIC", 0.8, 0.05),
        (("door", "hood", "bonnet", "fender", "roof", "trunk", "bumper", "body", "车门", "机盖", "翼子板", "车顶"), "BODY_PANEL", 0.84, 0.06),
    ]
    for words, label, confidence, critical_probability in rules:
        if any(word in text for word in words):
            part, part_confidence, critical = label, confidence, critical_probability
            break

    materials = state.get("materials") or []
    names = " ".join(str(material.get("name", "")) for material in materials).lower()
    metallic = max([float(material.get("metallic", 0.0)) for material in materials] or [0.0])
    transmission = max([float(material.get("transmission", 0.0)) for material in materials] or [0.0])
    emission = max([float(material.get("emission_strength", 0.0)) for material in materials] or [0.0])
    roughness_values = [float(material.get("roughness", 0.5)) for material in materials if "roughness" in material]
    roughness = sum(roughness_values) / len(roughness_values) if roughness_values else 0.5

    material_class, material_confidence = "OTHER", 0.45
    if part == "TIRE" or any(word in names for word in ("rubber", "tire", "tyre")):
        material_class, material_confidence = "RUBBER", 0.98
    elif part in {"HEADLAMP", "TAILLAMP"} or any(word in names for word in ("lens", "optical")):
        material_class, material_confidence = ("EMISSIVE" if emission > 0.05 else "OPTICAL"), 0.91
    elif part == "MIRROR" or "mirror" in names:
        material_class, material_confidence = "MIRROR", 0.95
    elif "chrome" in names or "镀铬" in names:
        material_class, material_confidence = "CHROME", 0.96
    elif part == "GLASS" or transmission > 0.45 or any(word in names for word in ("glass", "window", "windshield")):
        material_class, material_confidence = "GLASS", 0.93
    elif emission > 0.05:
        material_class, material_confidence = "EMISSIVE", 0.9
    elif any(word in names for word in ("paint", "carpaint", "body_paint", "车漆")):
        material_class, material_confidence = "PAINT", 0.93
    elif metallic > 0.7:
        material_class, material_confidence = "METAL", 0.86
    elif any(word in names for word in ("leather", "fabric", "alcantara", "皮革", "织物")) or part == "INTERIOR":
        material_class, material_confidence = "INTERIOR_SOFT", 0.82
    elif any(word in names for word in ("black", "abs", "plastic", "塑料")):
        material_class = "GLOSSY_PLASTIC" if roughness < 0.28 else ("BLACK_PLASTIC" if "black" in names else "MATTE_PLASTIC")
        material_confidence = 0.78

    return {
        "object_name": state.get("object_name", ""),
        "part_class": part,
        "part_confidence": part_confidence,
        "material_class": material_class,
        "material_confidence": material_confidence,
        "identity_critical_probability": critical,
        "identity_critical": critical >= 0.5,
        "backend": "LOCAL_FALLBACK",
        "error": error_text,
        "part_id_rgb": state.get("part_id_rgb", []),
        "part_id_index": state.get("part_id_index"),
    }


def _cache_key(state: dict[str, Any]) -> str:
    raw = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha1(raw.encode("utf-8", errors="replace")).hexdigest()


def resolve_object_semantics_batch(states: list[dict[str, Any]], batch_size: int = 10) -> list[dict[str, Any]]:
    if not states:
        return []
    results: list[dict[str, Any] | None] = [None] * len(states)
    pending = []
    for index, state in enumerate(states):
        key = _cache_key(state)
        with _CACHE_LOCK:
            cached = _CACHE.get(key)
        if cached is not None:
            results[index] = dict(cached)
        else:
            pending.append((index, state, key))

    for start in range(0, len(pending), max(1, int(batch_size))):
        group = pending[start:start + max(1, int(batch_size))]
        chunk = [state for _, state, _ in group]
        error_text = ""
        if _key():
            questions = {}
            for local_index in range(len(chunk)):
                target = f"objects[{local_index}]"
                questions[f"part_{local_index}"] = {
                    "type": "choice",
                    "instructions": f"Classify {target} as an automotive/product semantic part using names, hierarchy, dimensions, materials and Part-ID metadata. Choose OTHER if evidence is insufficient.",
                    "criteria": PART_CLASSES,
                }
                questions[f"material_{local_index}"] = {
                    "type": "choice",
                    "instructions": f"Classify the primary visual material of {target}. Use material names and Principled BSDF values. Distinguish optical lamp parts from ordinary glass.",
                    "criteria": MATERIAL_CLASSES,
                }
                questions[f"critical_{local_index}"] = {
                    "type": "noul",
                    "instructions": f"Is {target} an identity-critical asset such as a brand logo, wordmark, model text, readable plate text or readable screen UI that must not be redesigned?",
                    "criteria": {"true": "identity-critical and must preserve exact identity", "false": "ordinary part"},
                }
            try:
                data = _system_one({"objects": chunk}, questions, timeout=12.0)
                answers = data["answers"]
                for local_index, (global_index, state, key) in enumerate(group):
                    part = _choice(answers.get(f"part_{local_index}", {}))
                    material = _choice(answers.get(f"material_{local_index}", {}))
                    critical = _noul(answers.get(f"critical_{local_index}", {}))
                    row = {
                        "object_name": state.get("object_name", ""),
                        "part_class": part["choice"] or "OTHER",
                        "part_confidence": part["confidence"],
                        "material_class": material["choice"] or "OTHER",
                        "material_confidence": material["confidence"],
                        "identity_critical_probability": critical,
                        "identity_critical": critical >= 0.5,
                        "backend": "JEV",
                        "model": data.get("model", DEFAULT_MODEL),
                        "part_id_rgb": state.get("part_id_rgb", []),
                        "part_id_index": state.get("part_id_index"),
                    }
                    results[global_index] = row
                    with _CACHE_LOCK:
                        _CACHE[key] = dict(row)
                continue
            except Exception as exc:
                error_text = str(exc)

        for global_index, state, key in group:
            row = _local_object_semantics(state, error_text)
            results[global_index] = row
            with _CACHE_LOCK:
                _CACHE[key] = dict(row)

    return [row if row is not None else _local_object_semantics(states[index]) for index, row in enumerate(results)]


def semantic_prompt_block(results: list[dict[str, Any]], part_manifest: dict[str, Any] | None = None) -> str:
    if not results:
        return ""
    manifest = part_manifest or {}
    has_jev = any(row.get("backend") == "JEV" for row in results)
    title = "TypeSafe/Jev Semantic Part Map" if has_jev else "Local Semantic Fallback Map"
    critical = [row for row in results if row.get("identity_critical")]
    confident = [row for row in results if float(row.get("part_confidence", 0.0)) >= SEMANTIC_CONFIDENCE_THRESHOLD]
    ordered = (critical + [row for row in confident if row not in critical])[:28]
    lines = []
    for row in ordered:
        name = str(row.get("object_name", ""))
        rgb = row.get("part_id_rgb") or manifest.get(name, {}).get("rgb", [])
        rgb255 = []
        if isinstance(rgb, (list, tuple)) and len(rgb) >= 3:
            rgb255 = [max(0, min(255, int(round(float(value) * 255)))) for value in rgb[:3]]
        marker = "IDENTITY_CRITICAL" if row.get("identity_critical") else ""
        lines.append(
            f"- {name}: part={row.get('part_class','OTHER')}; material={row.get('material_class','OTHER')}; "
            f"confidence={float(row.get('part_confidence',0.0)):.2f}; Part-ID RGB={rgb255 or 'n/a'}; {marker}".rstrip("; ")
        )
    if not lines:
        return ""
    identity_rule = ""
    if critical:
        identity_rule = (
            "\n身份关键区域必须保持 Blender/参考资产的原始轮廓、字形、比例、朝向和位置；"
            "不得生成新的品牌符号、替换字母、拼错文字或把徽标风格化。视觉依据不足时宁可保留原始区域，也不要臆造。"
        )
    return (
        f"\n\n【{title}｜仅作为语义约束】\n"
        "下面的 Part-ID RGB 对应 Blender 的 Part-ID 控制图；伪彩色只用于定位，绝不能复制到最终渲染。\n"
        + "\n".join(lines)
        + identity_rule
        + "\n材质类别只用于区分车漆、橡胶、金属、塑料、光学件和发光件；不得因此改变 Blender 已锁定的几何边界。"
    )


def semantic_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    parts: dict[str, int] = {}
    materials: dict[str, int] = {}
    backends: dict[str, int] = {}
    critical = []
    for row in results:
        part = row.get("part_class", "OTHER")
        material = row.get("material_class", "OTHER")
        backend = row.get("backend", "UNKNOWN")
        parts[part] = parts.get(part, 0) + 1
        materials[material] = materials.get(material, 0) + 1
        backends[backend] = backends.get(backend, 0) + 1
        if row.get("identity_critical"):
            critical.append(row.get("object_name", ""))
    return {"parts": parts, "materials": materials, "backends": backends, "identity_critical": critical}
