# Wondful AI 渲染器 2.11

## 1. 提示词合并为唯一输入框

- 主面板只保留一个 `提示词` 输入框。
- 删除输入框下方重复的“完整提示词/自动换行预览”。
- 用户可以直接手动输入和修改。
- 点击 `AI 润色` 后，结果直接覆盖写回同一个输入框；完成后仍可继续手动修改，再点击 AI 渲染。
- 内部仍保留旧 `prompt_lines` 数据结构仅用于旧场景迁移，不再作为主 UI。

## 2. Unified Provider

`AI Provider` 现在同时决定：

- AI 润色
- 构图验收
- 最终生图

选择 `Codex`：整条链路使用 Codex / ChatGPT OAuth。

选择 `Antigravity`：整条链路使用 Antigravity CLI / Google OAuth，并通过内置 `generate_image` 工具生成或编辑最终图片。

不再出现“Antigravity 负责分析，但最终仍要求 Codex 登录”的默认跨 Provider 依赖。

## 3. Antigravity generate_image

- 使用 `agy` Headless 模式。
- 将 Camera Reference、Structure Guide、产品 Mask、产品/人物/风格参考和 edit base/mask 暂存到当前隔离 Render Session。
- 明确要求 Antigravity Agent 调用内置 `generate_image(Prompt, ImageName, ImagePaths)`。
- 使用 `stream-json` 捕获 `generate_image` tool step 和 `output_path`。
- 如果目标文件没有直接落在指定位置，会从 tool output / 当前 session 新生成位图中查找并复制到 Wondful 输出。
- 不使用 `--dangerously-skip-permissions`。

## 4. Provider 独立超时

新增：

- Antigravity 润色超时
- Antigravity 构图验收超时
- Antigravity 生图超时

默认 900 / 600 / 1800 秒；设置为 0 时插件不设置 subprocess 硬超时，并将 `agy --print-timeout` 放宽到长任务窗口。

## 5. 2.10 功能继续保留

- Camera Structure Lock：自动锁定当前 Scene Camera 画面内可见 Mesh，无需选择对象。
- 工程级可选渲染输出目录。
- 多参考图 + 剪贴板粘贴。
- Structure Guide / Product Mask / Anchor。
- 自动构图验收与局部修复。
- Wondful Compare。
