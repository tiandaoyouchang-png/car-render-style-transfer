# Wondful AI 渲染器 2.5

## 1. Wondful Compare 改为真正的对比画面

2.4 的 Compare 依赖 Image Editor GPU draw handler；部分 Blender / Workspace 状态下会出现“工作区创建了，但没有真正看到 AB 对比”的问题。

2.5 改为直接生成一个 Blender 内部 `Wondful_Compare_Preview` 对比图，因此进入 `Wondful Compare` 后即使没有启动任何 Modal/GPU Overlay，也会立即看到对比结果。

提供三种模式：

- **滑动**：左侧 Camera Reference，右侧 AI Render，支持滑杆和鼠标拖动。
- **叠加**：两张图按透明度叠加，重点检查轮心、车身外轮廓、地平线和透视是否重合。
- **差异**：显示两张图像素差异，快速定位构图漂移区域。

对比预览最长边限制为 1400px，只影响 Compare 工作区显示性能，不修改 Render Session 原始图片。

## 2. UI 重排

主侧栏重新分成五个层级：

1. 顶部紧凑状态：Codex、任务状态、当前 Camera、输出尺寸。
2. 创意提示词 + 两个主操作按钮。
3. 可折叠参考图区域，并显示各类数量。
4. 最新渲染结果 + 构图分数 + 大号“打开渲染对比”按钮。
5. 默认收起的高级设置。

账号详情、人物参考、风格参考、高级设置默认可收起，减少 N 面板纵向占用。

## 3. Compare 稳定性

- 新结果进入 Compare 时强制刷新当前 Render Session。
- 支持“重新载入当前 Session”。
- 旧的 `Wondful Compare` Workspace 可以直接复用，不要求手动删除。
- 鼠标拖动不再负责绘制本身，即使拖动 Modal 未启动，滑杆对比仍然有效。
