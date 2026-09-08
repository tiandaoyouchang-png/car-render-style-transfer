# Wondful AI Renderer 2.12

## Speed-first render pipeline

- 新增 **快速预览 / 标准 / 严格对齐** 三种渲染模式。
- **标准模式为默认**：一次点击 AI 渲染只做 1 次远程生图，不再自动追加远程构图验收。
- 快速预览：目标长边最多 1280px、1 次生图、不做远程验收。
- 严格对齐：保留 2.11 的生成后 AI 视觉验收、阈值判断和自动 Mask 修复重试。
- Camera Reference、Structure Guide、Product Mask 在三种模式下都继续参与结构约束。
- 计时统计按 fast / standard / strict 分开，避免严格模式的历史耗时污染标准模式 ETA。
- 结果面板新增远程“生图耗时 / 验收耗时”拆分显示。
