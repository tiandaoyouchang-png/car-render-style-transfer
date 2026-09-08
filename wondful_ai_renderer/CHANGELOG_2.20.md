# CHANGELOG 2.20 · Compare Workspace Guard

## Workspace 隔离修复

- 不再假设 `bpy.ops.workspace.duplicate()` 会自动切到新 Workspace。
- duplicate 前后比较 `bpy.data.workspaces`，精确识别新建副本。
- 只有新副本会被命名为 `Wondful Compare` 并改造成 Image Editor。
- Compare Workspace 写入 ownership tag，主工作区不会被复用或改写。
- 对 2.19 及更早版本造成的 `原布局被改名 + .001 副本` 提供证据充分时的保守恢复逻辑，旧 Workspace 不删除。

## Split 拖动

- 点击/按住后进入捕获状态，直到 LEFTMOUSE RELEASE 才结束。
- 拖动期间允许鼠标离开图片区域，分割位置会 clamp 到 0–1。
- 初始抓取热区扩展 28px，减少高 DPI 下命中失败。
- 预览刷新节流到约 30 FPS，减少 NumPy 合成 + pixel upload 对 UI 事件循环的阻塞。
- 分割线视觉宽度由 2px 增加到 4px。

## 保留

- 2.19 Product Collection Structure Lock。
- 2.18 Style Reference Refresh Fix。
- 2.17 Single Prompt + Inline Progress。
