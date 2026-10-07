# Wondful AI Renderer 2.13

## Multiline Prompt Editor

- 提示词区域改为真正的多行编辑 UI，不再只显示单行 StringProperty。
- AI 润色结果仍写回同一个提示词内容，并自动拆分为可编辑的视觉行。
- 手动修改任意行会实时同步回唯一 canonical prompt。
- 新增“编辑区高度”3–12 行，可直接拖动数值或使用箭头放大/缩小。
- 支持新增/删除编辑行；渲染时始终读取当前编辑器中的最新内容。
- 保留 2.12 的快速预览 / 标准 / 严格对齐和统一 Provider 逻辑。
