# Wondful AI Renderer 2.16 - Workflow UI

## 主界面按操作顺序重排

主流程调整为：

`Provider / Camera → 提示词 → AI 润色 / 重新生成提示词 → 参考图 → AI 渲染 → 输出 → 最新结果 → 高级设置`

- `AI 渲染` 从提示词卡片移动到参考图之后。
- 渲染模式与 Camera Structure Lock 与最终渲染按钮放在同一渲染卡片中。
- 输出目录移动到渲染按钮之后，减少主界面前后跳读。

## 登录 UI 收纳

- 当前 Provider **已登录**时，主界面不再显示登录状态行、刷新按钮与账号详情。
- 已登录账号的检测、Codex 退出登录和 OAuth 说明收进 `高级设置`。
- 当前 Provider **未登录 / 未检测 / CLI 缺失 / 异常**时，仍保持顶部显眼账号状态与登录入口，方便立即恢复。

## 提示词自适应高度

- 移除 `高度 5` 数字调节。
- 提示词 1–5 个可视行时，编辑区按实际内容自动增高。
- 超过 5 行时默认只显示 5 行，并显示 `展开全文 · N 行`。
- 展开后显示完整提示词行数，可随时 `收起`。
- AI 润色仍写回同一个 canonical Prompt，多行编辑与最终渲染读取同一份内容。

## 保留

- 2.14 Style Refresh Guard：更换风格图后必须先重新生成提示词，再允许 AI 渲染。
- 2.15 UI draw 只读修复。
- FAST / STANDARD 单次生图与 STRICT 构图验收策略。
- Codex / Antigravity Unified Provider。
