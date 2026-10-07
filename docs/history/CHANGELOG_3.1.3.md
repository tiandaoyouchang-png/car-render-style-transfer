# 3.1.3 更新记录

## 核心方向

3.1.3 将 3.1.2 中“TypeSafe 风格的本地规则”升级为真正可调用 TypeSafe System One / Jev 的语义层，同时保持 Blender 作为几何、相机和构图的唯一结构权威。Jev 只做结构化语义判断，Codex / Antigravity 仍负责复杂提示词推理和最终图像生成。

## 新增

- **真实 Jev 后端**
  - 通过官方 TypeSafe System One HTTP API `/v1/systemone` 调用 `jev-latest`。
  - 使用 `TYPESAFE_API_KEY`、`TYPESAFE_BASE_URL`、`TYPESAFE_DEFAULT_MODEL` 环境变量。
  - 无 Key、网络错误、超时或服务失败时自动切换 `LOCAL_FALLBACK`，不阻断 Blender 渲染。
  - 插件不在 .blend 中保存 TypeSafe API Key。

- **Semantic Part Map**
  - 从 Blender 产品集合提取对象名、父子关系、Collection、世界位置、尺寸、Mesh 复杂度、材质名和 Principled BSDF 参数。
  - Jev 将对象分类为 BODY_PANEL / GLASS / TIRE / WHEEL / BRAKE / HEADLAMP / TAILLAMP / MIRROR / LOGO_BADGE / TEXT_BADGE / CHROME_TRIM / BLACK_PLASTIC / INTERIOR / SCREEN_UI / SENSOR / PLATE / OTHER。
  - 语义结果与原有 Part-ID RGB 建立映射，并在最终生图 Prompt 中明确告诉生成模型每个关键区域的职责。

- **Material Semantic Resolver**
  - Jev 分类 PAINT / GLASS / RUBBER / METAL / CHROME / BLACK_PLASTIC / GLOSSY_PLASTIC / MATTE_PLASTIC / INTERIOR_SOFT / EMISSIVE / OPTICAL / MIRROR / OTHER。
  - 用于改善 Rubber vs Plastic、Metal vs Black Plastic、Lamp vs Glass 等汽车常见歧义。

- **Identity Critical Asset Lock**
  - 自动识别 Logo、品牌/车型字标、车牌字符和可读屏幕 UI。
  - 这些区域被写入生成约束：保持原始轮廓、字形、比例、朝向和位置，不允许生图模型重新设计、拼错或风格化。
  - UI 显示本次检测出的身份关键资产名称。

- **Change Scope / Appearance Judgments**
  - AI 润色前，Jev 一次请求判断主题、光影反差、整体材质高光、细节密度、修改范围、是否保留身份资产、是否真的请求了结构变化。
  - 结构化结论作为 Codex / Antigravity 提示词润色的前置约束，而不是替代视觉参考图。

- **参考图批量分类**
  - PRODUCT / STYLE / PERSON / MIXED / UNSURE。
  - 所有参考图通过一次 Jev 请求批量判断，减少延迟和 token。
  - 低置信度、MIXED 或 UNSURE 不自动搬动，保留原分类。
  - 若目标分类达到每类 8 张上限，自动保留原分类，避免丢图。
  - 使用 Stage -> Validate -> Commit；API 中途失败不会先清空 Blender 参考图集合。

## 修正

- **停用误导性的“TypeSafe 候选图视觉评分”**
  - 3.1.2 的候选评分仅使用文件大小/分辨率，不是真实的构图、材质或美学评价。
  - 3.1.3 不再用该分数选择最佳候选。
  - 候选选择继续依据真实 Canvas 检查和严格模式的远程视觉 Alignment Audit。

- **Jev 线程安全**
  - 所有 bpy / Blender 数据读取都在主线程完成并转换为纯 JSON 状态。
  - 后台线程只向 Jev 发送 JSON，不访问 bpy 数据块。

## 配置

macOS / Linux:

```bash
export TYPESAFE_API_KEY="ts_..."
export TYPESAFE_DEFAULT_MODEL="jev-latest"
```

如需永久生效，可写入启动 Blender 的 shell 环境。未配置 Key 时插件仍可运行，但 UI 会明确显示 `LOCAL_FALLBACK`。

## 设计边界

- Blender = Geometry / Camera / Composition truth
- Jev = semantic judgment / routing / confidence
- Codex or Antigravity = complex reasoning + prompt orchestration
- Image generation = final appearance rendering

Jev 不直接看图，不承担构图视觉验收，也不替代最终图像模型。
