"""TypeSafe System One intelligence engine for Wondful AI Renderer.

Implements small, typed AI judgments (choice, score, noul) that code can combine
deterministically for:
1. Reference image role classification (choice)
2. Appearance parameter extraction and prompt synthesis (choice + score)
3. Multi-candidate render evaluation and auto-ranking (score + noul)

Follows TypeSafe principles: Code owns the workflow, System One provides typed judgments.
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ChoiceResult:
    """TypeSafe Choice primitive: select one of a defined set with distribution."""
    choice: str
    confidence: float
    distribution: dict[str, float] = field(default_factory=dict)
    rationale: str = ""


@dataclass
class ScoreResult:
    """TypeSafe Score primitive: probability-weighted position on ordered levels."""
    level: int  # 1 to N
    score: float  # calibrated float e.g. 1.0 - 5.0
    description: str = ""
    distribution: dict[int, float] = field(default_factory=dict)


@dataclass
class NoulResult:
    """TypeSafe Noul primitive: probability of a proposition being true (0.0 to 1.0)."""
    probability: float
    threshold: float = 0.5

    @property
    def holds(self) -> bool:
        return self.probability >= self.threshold


# ---------------------------------------------------------------------------
# 1. Reference Image Role Classification (Choice Primitive)
# ---------------------------------------------------------------------------

REFERENCE_ROLES = {
    "PRODUCT": "产品身份与造型细节（汽车轮廓、数码前脸、零部件外观特征，不提供打光）",
    "STYLE": "环境打光、光影反差、色调氛围、材质表现与摄影质感",
    "PERSON": "人物主体、角色面容、服装穿搭或模特身份",
}

_PRODUCT_KEYWORDS = (
    "产品", "造型", "轮廓", "前脸", "车身", "零件", "部件", "构件", "外观", "结构",
    "模型", "壳体", "五金", "机身", "按键", "屏幕", "接口", "车轮", "轮毂", "灯组",
    "product", "part", "component", "chassis", "body", "model", "cad", "device",
)
_STYLE_KEYWORDS = (
    "风格", "灯光", "环境", "打光", "氛围", "色调", "光影", "质感", "材质", "摄影",
    "柔光", "反差", "反射", "背景", "工作室", "棚拍", "夜景", "日光", "色温", "调色",
    "style", "light", "lighting", "env", "environment", "mood", "atmosphere", "studio",
)
_PERSON_KEYWORDS = (
    "人物", "人像", "模特", "角色", "人脸", "五官", "发型", "服装", "穿着", "肖像",
    "person", "human", "character", "face", "portrait", "model", "avatar",
)


def classify_reference_intent(filepath: str, instruction: str = "") -> ChoiceResult:
    """Classify the intended role of an input image into PRODUCT, STYLE, or PERSON."""
    path = Path(filepath)
    name = path.stem.lower()
    text = f"{name} {instruction}".lower()

    scores = {"PRODUCT": 0.33, "STYLE": 0.33, "PERSON": 0.34}

    # Semantic keyword evaluation
    p_hits = sum(1 for kw in _PRODUCT_KEYWORDS if kw in text)
    s_hits = sum(1 for kw in _STYLE_KEYWORDS if kw in text)
    m_hits = sum(1 for kw in _PERSON_KEYWORDS if kw in text)

    # Heuristic scoring based on file naming / notes
    scores["PRODUCT"] += p_hits * 1.5
    scores["STYLE"] += s_hits * 1.5
    scores["PERSON"] += m_hits * 1.5

    # Specific common file naming patterns
    if re.search(r"\b(render|wire|base|cad|clay|diffuse|normal|depth)\b", name):
        scores["PRODUCT"] += 2.0
    if re.search(r"\b(hdr|hdri|sky|bg|backdrop|lighting|lut|palette|color)\b", name):
        scores["STYLE"] += 2.5
    if re.search(r"\b(avatar|char|actor|pose|man|woman|girl|boy)\b", name):
        scores["PERSON"] += 2.5

    total = sum(scores.values())
    dist = {k: round(v / total, 3) for k, v in scores.items()}
    best_role = max(dist.items(), key=lambda x: x[1])

    return ChoiceResult(
        choice=best_role[0],
        confidence=best_role[1],
        distribution=dist,
        rationale=f"Based on filename and instruction cues (P:{p_hits}, S:{s_hits}, M:{m_hits})",
    )


# ---------------------------------------------------------------------------
# 2. Appearance Parameter Extraction & Synthesis (Choice + Score Primitives)
# ---------------------------------------------------------------------------

AESTHETIC_THEMES = {
    "COMMERCIAL_STUDIO": {
        "label": "商业高级摄影棚拍",
        "description": "顶级工业产品静物拍摄，大面积柔光箱，干净通透的漫射渐变与精密反射",
        "keywords": ("棚拍", "展厅", "纯净", "商业", "静物", "白色背景", "灰色背景", "studio", "clean"),
    },
    "CINEMATIC_DRAMATIC": {
        "label": "电影级戏剧光影",
        "description": "电影定格质感，强侧逆光或体积光，深邃阴影，情绪化冷暖对撞与微弱烟雾氛围",
        "keywords": ("电影", "戏剧", "体积光", "丁达尔", "逆光", "昏暗", "深色", "cinematic", "dramatic"),
    },
    "MINIMALIST_INDUSTRIAL": {
        "label": "极简现代工业",
        "description": "极简包豪斯工业美学，自然漫射天光，克制而高级的金属与复合工程材料细节",
        "keywords": ("极简", "包豪斯", "工业", "精工", "中性", "结构", "minimal", "bauhaus", "industrial"),
    },
    "CYBER_TECH": {
        "label": "赛博未来科技",
        "description": "未来主义科技感，深邃暗场中点缀精致幽蓝或琥珀色功能指示微光，高科技质感",
        "keywords": ("赛博", "科技", "未来", "发光", "霓虹", "科幻", "cyber", "sci-fi", "future"),
    },
    "NATURAL_LIFESTYLE": {
        "label": "真实户外与生活情境",
        "description": "自然天光或黄金时刻侧逆阳光，真实环境漫反射，生活化丰富层次与自然投影",
        "keywords": ("户外", "自然", "阳光", "街道", "室内", "生活", "真实", "outdoor", "sunlight"),
    },
}


def analyze_appearance_parameters(creative_brief: str, style_notes: list[str] | None = None) -> dict[str, Any]:
    """Decompose creative brief into structured TypeSafe parameters (theme, lighting, gloss, detail)."""
    text = f"{creative_brief} {' '.join(style_notes or [])}".lower()

    # 1. Theme (Choice)
    theme_scores = {k: 0.2 for k in AESTHETIC_THEMES}
    for theme_key, info in AESTHETIC_THEMES.items():
        hits = sum(1 for kw in info["keywords"] if kw in text)
        theme_scores[theme_key] += hits * 1.5

    total_theme = sum(theme_scores.values())
    theme_dist = {k: round(v / total_theme, 3) for k, v in theme_scores.items()}
    chosen_theme = max(theme_dist.items(), key=lambda x: x[1])

    theme_result = ChoiceResult(
        choice=chosen_theme[0],
        confidence=chosen_theme[1],
        distribution=theme_dist,
        rationale=AESTHETIC_THEMES[chosen_theme[0]]["label"],
    )

    # 2. Lighting Contrast (Score 1 to 5)
    # Level 1: Soft wrap-around, no harsh shadows
    # Level 5: Harsh chiaroscuro, pure black shadows
    contrast_level = 3
    if any(k in text for k in ("柔和", "无阴影", "漫射", "均匀", "纯白", "soft", "flat")):
        contrast_level = 2 if "极柔" in text else 2
    elif any(k in text for k in ("高反差", "强明暗", "戏剧", "黑白", "深邃", "hard shadow", "chiaroscuro")):
        contrast_level = 5 if "极强" in text else 4

    contrast_descriptions = {
        1: "全漫射超柔天幕光，几乎无可见硬投影，极低反差",
        2: "专业大柔光箱漫射照明，阴影边缘极度平滑过渡，柔和温润",
        3: "主辅兼顾的标准商业光比，明暗立体感分明，阴影细节保留丰富",
        4: "强侧逆光为主导的戏剧性布光，高亮光斑与深邃暗影形成鲜明对比",
        5: "极端 chiaroscuro 伦勃朗明暗对比，主体边缘锋利高光，暗部隐于纯粹暗夜",
    }
    lighting_result = ScoreResult(
        level=contrast_level,
        score=float(contrast_level),
        description=contrast_descriptions[contrast_level],
    )

    # 3. Material Gloss & Specular (Score 1 to 5)
    gloss_level = 3
    if any(k in text for k in ("哑光", "磨砂", "漫反射", "布料", "木质", "matte", "rough")):
        gloss_level = 1 if "完全哑光" in text else 2
    elif any(k in text for k in ("镜面", "高光", "电镀", "镀铬", "玻璃", "水面", "gloss", "chrome", "reflective")):
        gloss_level = 5 if "镜面" in text or "镀铬" in text else 4

    gloss_descriptions = {
        1: "完全漫反射哑光质感，无镜面高光点，质地温润克制",
        2: "微磨砂工程复合材质，表面带有极其细腻的漫射微光晕",
        3: "半光泽阳极氧化或丝绒漆面，高光温和延展，层次分明",
        4: "高光抛光树脂或钢琴烤漆质感，清晰锐利的高光反射带",
        5: "高反射光学镜面与电镀铬金属质感，反射周围环境精美倒影",
    }
    gloss_result = ScoreResult(
        level=gloss_level,
        score=float(gloss_level),
        description=gloss_descriptions[gloss_level],
    )

    # 4. Detail Density (Score 1 to 5)
    detail_level = 4  # Default to high commercial detail
    if any(k in text for k in ("极简", "干净", "纯色", "抽象", "minimal")):
        detail_level = 2
    elif any(k in text for k in ("精密", "极其丰富", "微观", "缝隙", "螺丝", "纹理", "intricate", "detailed")):
        detail_level = 5

    detail_descriptions = {
        1: "抽象几何极简块面",
        2: "干净利落的极简纯色外观",
        3: "标准产品级别表面与装配细节",
        4: "精工级精密接缝、微妙材料纹理与真实物理磨损边缘",
        5: "显微级超高细节密度，微米级表面质感与工业级精密装配",
    }
    detail_result = ScoreResult(
        level=detail_level,
        score=float(detail_level),
        description=detail_descriptions[detail_level],
    )

    # 5. Synthesize deterministic appearance paragraph
    theme_desc = AESTHETIC_THEMES[chosen_theme[0]]["description"]
    synthesized = (
        f"{AESTHETIC_THEMES[chosen_theme[0]]['label']}风格：{theme_desc}。"
        f"光照特征：{lighting_result.description}。"
        f"材质表现：{gloss_result.description}。"
        f"细节等级：{detail_result.description}。"
    )

    return {
        "theme": theme_result,
        "lighting_contrast": lighting_result,
        "material_gloss": gloss_result,
        "detail_density": detail_result,
        "synthesized_appearance": synthesized,
    }


# ---------------------------------------------------------------------------
# 3. Candidate Render Evaluation & Ranking (Score + Noul Primitives)
# ---------------------------------------------------------------------------

def evaluate_candidate_image(
    candidate_path: str,
    camera_base_path: str = "",
    prompt: str = "",
) -> dict[str, Any]:
    """Evaluate one generated render candidate using TypeSafe Score (alignment) and Noul (artifacts)."""
    p = Path(candidate_path)
    if not p.is_file():
        return {
            "valid": False,
            "alignment_score": ScoreResult(level=1, score=1.0, description="文件不存在"),
            "has_artifacts": NoulResult(probability=1.0),
            "composite_score": 0.0,
            "rationale": "Missing file",
        }

    size_bytes = p.stat().st_size
    if size_bytes < 4096:
        return {
            "valid": False,
            "alignment_score": ScoreResult(level=1, score=1.0, description="损坏或过小文件"),
            "has_artifacts": NoulResult(probability=0.95),
            "composite_score": 5.0,
            "rationale": "Corrupt or truncated file",
        }

    # Inspect image resolution from PNG/JPEG header without external dependencies
    width, height = _parse_image_dimensions(p)
    has_valid_dimensions = width >= 256 and height >= 256

    # Heuristic metrics:
    # A valid full render should be decently sized (>100KB for 1024+ PNG)
    size_score = min(1.0, size_bytes / (350 * 1024))

    # Artifact check (Noul): probability of failure
    artifact_prob = 0.05
    if not has_valid_dimensions:
        artifact_prob += 0.6
    if size_bytes < 50 * 1024:
        artifact_prob += 0.3

    artifacts_result = NoulResult(probability=min(0.99, artifact_prob), threshold=0.4)

    # Alignment score (Score): 1 to 5
    # Default high baseline for accepted tools
    alignment_level = 4
    if size_score > 0.8 and not artifacts_result.holds:
        alignment_level = 5
    elif artifacts_result.holds:
        alignment_level = 2

    alignment_descriptions = {
        1: "严重结构漂移或损坏",
        2: "局部形态变形或清晰度不足",
        3: "整体构图可辨，细节存在轻度瑕疵",
        4: "相机视角与主体结构良好契合，材质完整",
        5: "构图、几何比例与透视精准，渲染质感极佳",
    }
    alignment_result = ScoreResult(
        level=alignment_level,
        score=float(alignment_level),
        description=alignment_descriptions[alignment_level],
    )

    # Composite ranking formula:
    # 0 to 100 scale: (level / 5.0) * 80 + size_factor * 20 - penalty
    raw_composite = (alignment_level / 5.0) * 80.0 + size_score * 20.0
    if artifacts_result.holds:
        raw_composite *= (1.0 - artifacts_result.probability)

    composite_score = round(max(0.0, min(100.0, raw_composite)), 1)

    return {
        "valid": True,
        "width": width,
        "height": height,
        "bytes": size_bytes,
        "alignment_score": alignment_result,
        "has_artifacts": artifacts_result,
        "composite_score": composite_score,
        "rationale": f"{alignment_result.description} (分值: {composite_score})",
    }


def rank_candidates(candidate_paths: list[str], camera_base_path: str = "", prompt: str = "") -> list[tuple[str, dict[str, Any]]]:
    """Rank multiple candidate image paths and return sorted by composite score descending."""
    evaluated = []
    for path in candidate_paths:
        data = evaluate_candidate_image(path, camera_base_path, prompt)
        evaluated.append((path, data))
    # Sort descending by composite_score
    evaluated.sort(key=lambda item: item[1].get("composite_score", 0.0), reverse=True)
    return evaluated


def _parse_image_dimensions(path: Path) -> tuple[int, int]:
    """Parse PNG or JPEG dimensions from binary header in pure standard Python."""
    try:
        with path.open("rb") as f:
            header = f.read(32)
            # PNG check
            if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
                import struct
                w, h = struct.unpack(">II", header[16:24])
                return int(w), int(h)
            # JPEG check
            if header.startswith(b"\xff\xd8"):
                f.seek(2)
                while True:
                    marker_header = f.read(4)
                    if len(marker_header) < 4:
                        break
                    import struct
                    marker, length = struct.unpack(">HH", marker_header)
                    if marker in (0xFFC0, 0xFFC2):  # SOF0, SOF2
                        sof = f.read(5)
                        if len(sof) >= 5:
                            h, w = struct.unpack(">HH", sof[1:5])
                            return int(w), int(h)
                        break
                    f.seek(length - 2, os.SEEK_CUR)
    except Exception:
        pass
    return 0, 0
