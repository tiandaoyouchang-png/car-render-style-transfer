# Changelog

## 3.1.7 · Prompt & Appearance Lock（2026-10-07）

围绕“给参考图 → AI 写提示词”流程的六项优化。参考职责规则版本升到 2，已润色过的旧工程会提示重新生成一次提示词。

### 新增
- **配色来源**：新增「Blender 材质 / 产品参考图 / 仅文字」三选一，默认 Blender 材质。插件读取产品集合的 Principled BSDF（贴图取平均色、Mix 乘色、绒面光泽色、金属度、粗糙度、清漆），写成“产品外观锁定”原样进入生图指令。此前规则禁止从产品图取颜色，提示词没写颜色时固有色可能跑偏。任何来源都不会采用产品照片的打光。
- **产品外观锁定**：单独的「产品外观」字段（如“厚清漆、长而柔的渐变高光”），换环境参考时不被重写，多场景之间产品质感保持一致；AI 润色只负责环境、光影与氛围。
- **必须保留的细节清单**：合并「保留细节」字段、产品参考图的「造型重点」和 Jev 识别出的身份资产，写进生图指令；构图验收时逐项检查，缺失项写入 `missing_details` 并追加到纠偏指令。
- **环境分析可见可改**：环境／风格参考图的分析结果（主光方向、色温、软硬、氛围）在面板中显示并可编辑，下次润色使用修改后的内容。
- **主光标识**：环境参考第一张标为「主光来源」，其余为「辅助」，可用箭头调整顺序。

### 修复
- **提示词过滤器误删外观描述**：旧过滤器只要一句话同时出现“位置/透视/地平线”和“保持/一致/必须”就整句删除，例如“高光位置与环境主光一致”“地平线处的天空保持暖橙色”“车标位置的镀铬质感必须清晰”。现按分句处理，区分硬结构词（构图、机位、裁切…）和软结构词，带光影/材质词的分句保留；被移除的片段显示在提示词下方。

### 工程
- 新增 `wondful_ai_renderer/appearance_lock.py`、`tests/test_317_prompt_flow.py`（11 项）；离线测试共 33 项通过。
- Blender 4.3.2 实机：`tools/blender_acceptance.py` 全部通过；用 Khronos SheenChair 实测材质读取（正确识别橙红色绒面 + 深棕木腿）与面板绘制。

## 3.1.6 · Blender 5 Compatibility（2026-10-07）

稳定性版本，不改变工作流与提示词规则。

### 修复
- **Blender 5.x 原生结构图失效**：5.0 起合成器改为节点组（`scene.compositing_node_group`），`scene.node_tree` 被移除，File Output 节点改为 `directory / file_name / file_output_items`，Object Index 输出改名为 `Object Index`，EXR 需先设 `media_type`。3.1.5 在 5.x 上会抛 `AttributeError` 后静默退回投影方案，导致没有 Depth / Normal / Part ID，Identity Preserve Mask 无法生成。现兼容 4.x 与 5.x 两套 API。
- **EEVEE 标识符**：4.2–4.x 为 `BLENDER_EEVEE_NEXT`，5.x 为 `BLENDER_EEVEE`，按可用项自动选择；`WONDFUL_STRUCTURE_ENGINE` 环境变量可覆盖（无 GPU 的 CI 用 `CYCLES`）。
- **Depth 图全白**：背景像素深度为 1e10，旧过滤阈值 1e20 让其参与归一化，far 被拉到 1e10。现只统计相机 clip_end 以内的真实几何，并且深度窗口以产品像素为准（外扩 35%）。真实 Ferrari 458 模型测试中，大地面曾把车身压进顶部约 13% 的灰度；修复后车身占满整个灰度范围，manifest 另记 `scene_depth_range`。
- **Antigravity 成功后 NameError**（3.1.2 起）：`conversation_ids` 定义在内部函数却在外部使用，图片已生成插件却报失败。
- **严格纠偏 Mask 尺寸**：身份修复 Mask 现按上一轮候选图实际尺寸重采样（缩小时保守取并集，细 Logo 笔画不丢失）。
- **5.x 输出格式恢复**：相机截图临时切到 PNG 时同时保存/恢复 `media_type`，用户输出为 EXR 多层时不再报错。

### 工程
- 新增 `tests/test_316_regressions.py`（11 项）、`depth_utils.py`、`tools/check_undefined_names.py`、`tools/blender_acceptance.py`（Blender 实机验收），CI 增加未定义名称检查。
- 历史 CHANGELOG / 测试报告移至 `docs/history/`，不再随插件安装。
- 新增 `tools/build_release.py` 生成可安装 ZIP。
- README 中的安装步骤与测试说明更新为实际情况（此前写 3.1.1 安装包与 144 项测试，仓库中实际为 11 项）。
