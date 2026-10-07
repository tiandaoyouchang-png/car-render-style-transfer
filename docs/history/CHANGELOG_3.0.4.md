# 3.0.4 · Editable Prompt Fix

## 修复

- 修复 Blender 5.2+ 原生多行提示词输入框无法持续输入的问题。
- 根因：`prompt` 的 update callback 在每次按键后重建 `prompt_lines` Collection，导致原生 `UILayout.textbox` 编辑焦点被 UI 数据刷新打断。
- Blender 5.2+ 现在直接编辑唯一的 `props.prompt`，输入期间不再触碰兼容层 Collection。
- Blender 4.3-5.1 才继续维护 `prompt_lines` 兼容编辑器。
- AI 润色 / 重新生成提示词仍然直接写回同一个 canonical Prompt。

## 不变

- 提示词只负责 Appearance，不承担构图约束。
- 参考图仍位于 AI 润色按钮之前，每张参考图保留“参考什么”输入。
- Structure Packet 继续承担 Camera / Composition / Geometry / Position / Scale / Occlusion 等结构约束。
