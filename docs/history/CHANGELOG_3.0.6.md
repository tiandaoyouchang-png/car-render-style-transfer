# 3.0.6 · Unified Prompt + AGY Auth Fix

## 总提示词编辑器
- `props.prompt` 是唯一 Canonical Prompt；旧 `prompt_lines` 只保留旧工程迁移兼容，不再作为主编辑界面。
- 不再使用“一行一个 StringProperty”的假多行编辑器。
- 运行中的 Blender 只要提供 `UILayout.textbox` 就直接启用真正的单一多行、可滚动输入框，不再硬编码 Blender 版本判断。
- 对 Blender 5.1 / 4.x 等没有 Panel 原生多行 textbox 的版本，显示单一 Prompt 区域和“编辑完整提示词”入口；点击后打开独立 Text Editor 窗口，支持整段编辑、自动换行和滚动，并自动同步回插件唯一 Prompt。

## Antigravity 登录识别
- 修复 agy CLI 已完成 Google OAuth 且 JSON 返回 `status: SUCCESS`，插件却仍因为缺少固定响应字符串而判定未登录的问题。
- Headless 探测现在以 agy 官方 JSON envelope 的 `SUCCESS` 为登录可用依据。
- `denied_actions` 中无关的工具拒绝（例如 `ListDir`）不再被当成 OAuth 失效。
