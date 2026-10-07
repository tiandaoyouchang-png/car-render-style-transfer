# Wondful AI 渲染器 3.0 测试报告

## 已执行

- 17 个 Python 模块 `py_compile`：通过。
- 17 个 Python 模块 AST 解析：通过。
- `build_render_prompt()` Structure Packet Reference 编号测试：通过。
- 2.21 UI 收尾逻辑已保留：风格冗余提示移除；相机/分辨率位于 Structure Lock。
- 静态检查确认：3.0 使用 `build_structure_packet()`，不再默认发送旧的 dense wireframe guide。
- 静态检查确认：Standard/Strict 的 Reference 顺序由 `generation_reference_roles` 与实际附件列表共同生成。
- 静态检查确认：严格模式首轮以 Camera Base 作为 edit base，修复轮次继续使用 Product Edit Mask。
- 静态检查确认：临时修改的 Object `pass_index` 在 `finally` 中恢复。

## 需要 Blender 实机验证

当前环境未安装 Blender GUI/Runtime，因此以下内容需要安装插件后验证：

1. EEVEE Next 临时 Scene 能否在你的 Blender 版本/模型上稳定输出 Depth / Normal / IndexOB。
2. 97+ Mesh 的产品 Collection 原生 Pass 生成耗时。
3. `product_edit_mask.png` 与 1920×1080 / 竖版 Camera Base 的像素对齐。
4. Codex / Antigravity 对 Mask / Depth / Normal / Silhouette 多参考的实际服从程度。
5. Strict 模式的局部纠偏是否能稳定保留背景与已有材质。

如果原生 Pass 失败，`07_structure.json` / `structure_control.json` 会记录 `native_pass_error`，并自动回退到 2.x 投影方案。


## 3.0.1 Prompt Editor

- [x] Python modules compile.
- [x] Prompt fallback soft-wrap roundtrip preserves canonical text.
- [x] Prompt header displays character count only.
- [x] Expand/collapse / line-count UI removed from the main panel.
- [x] Blender 5.2+ native textbox path retained.
- [x] Blender 4.3–5.1 fallback uses a scrollable UIList container.
- [ ] Real Blender visual interaction must still be verified in the user's exact Blender version.

## 3.0.2 Reference Instructions checks

- `py_compile` / AST：17 个 Python 模块通过。
- UI 静态顺序：参考图区域位于 AI 润色/重新生成提示词按钮之前。
- 每个 `WONDFUL_ReferenceItem` 有独立 `instruction` 字段。
- Prompt Engine：产品 / 人物 / 风格逐图参考重点写入对应 Reference 说明。
- 风格分析：逐张风格参考重点进入独立 style-analysis 请求。
- Render Prompt：逐图参考重点继续传入最终生图指令。
- 风格参考重点编辑会使 style prompt dirty，要求重新生成提示词。

## 3.0.3 验证

- 17 个 Python 模块通过 py_compile / AST。
- 参考图区域位于 AI 润色按钮之前。
- 每张参考图有“参考什么”输入框，指令进入 Prompt 与 Render Reference 映射。
- AI 润色输出经过 Appearance sanitizer：构图、机位、bbox、轮心坐标、zoom/pan/crop 等结构约束句会被移除。
- 最终 render wrapper 不再写具体构图数值，只保留 Structure Packet 各控制图的角色说明。

## 3.0.4 Editable Prompt regression
- `py_compile`: 17 Python modules passed.
- AST parse: 17 modules passed.
- Static guard: Blender 5.2+ `_prompt_value_update` returns before legacy `prompt_lines` rebuild.
- Native `UILayout.textbox` remains bound directly to canonical `props.prompt`.
- Blender 4.3-5.1 fallback sync path remains present.
- Real Blender GUI typing still requires user-side runtime verification.

## 3.0.6 回归
- [x] 17 个 Python 模块 py_compile 通过。
- [x] 17 个模块 AST 通过。
- [x] 总 Prompt UI 不再调用 `WONDFUL_UL_prompt_lines` 主编辑器。
- [x] `UILayout.textbox` 改为能力检测；有原生能力即使用单一多行滚动输入框。
- [x] 旧 Blender fallback 改为独立 Text Editor，自动同步 canonical `props.prompt`。
- [x] AGY `status=SUCCESS` + `denied_actions=ListDir` 模拟探测判定为已登录。
