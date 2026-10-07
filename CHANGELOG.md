# Changelog

## 3.1.6 · Blender 5 Compatibility（2026-10-07）

稳定性版本，不改变工作流与提示词规则。

### 修复
- **Blender 5.x 原生结构图失效**：5.0 起合成器改为节点组（`scene.compositing_node_group`），`scene.node_tree` 被移除，File Output 节点改为 `directory / file_name / file_output_items`，Object Index 输出改名为 `Object Index`，EXR 需先设 `media_type`。3.1.5 在 5.x 上会抛 `AttributeError` 后静默退回投影方案，导致没有 Depth / Normal / Part ID，Identity Preserve Mask 无法生成。现兼容 4.x 与 5.x 两套 API。
- **EEVEE 标识符**：4.2–4.x 为 `BLENDER_EEVEE_NEXT`，5.x 为 `BLENDER_EEVEE`，按可用项自动选择；`WONDFUL_STRUCTURE_ENGINE` 环境变量可覆盖（无 GPU 的 CI 用 `CYCLES`）。
- **Depth 图全白**：背景像素深度为 1e10，旧过滤阈值 1e20 让其参与归一化，far 被拉到 1e10。现只统计相机 clip_end 以内的真实几何。
- **Antigravity 成功后 NameError**（3.1.2 起）：`conversation_ids` 定义在内部函数却在外部使用，图片已生成插件却报失败。
- **严格纠偏 Mask 尺寸**：身份修复 Mask 现按上一轮候选图实际尺寸重采样（缩小时保守取并集，细 Logo 笔画不丢失）。
- **5.x 输出格式恢复**：相机截图临时切到 PNG 时同时保存/恢复 `media_type`，用户输出为 EXR 多层时不再报错。

### 工程
- 新增 `tests/test_316_regressions.py`（9 项）、`tools/check_undefined_names.py`、`tools/blender_acceptance.py`（Blender 实机验收），CI 增加未定义名称检查。
- 历史 CHANGELOG / 测试报告移至 `docs/history/`，不再随插件安装。
- 新增 `tools/build_release.py` 生成可安装 ZIP。
- README 中的安装步骤与测试说明更新为实际情况（此前写 3.1.1 安装包与 144 项测试，仓库中实际为 11 项）。
