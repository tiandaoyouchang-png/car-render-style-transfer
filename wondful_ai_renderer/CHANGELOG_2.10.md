# Wondful AI 渲染器 2.10 · Camera Structure Lock + Codex Timeout Fix

## 关键修复

### 1. Structure Lock 改为 Camera 驱动

- 删除“锁定当前选中 / 清除结构对象”工作流。
- 用户无需选择车辆或任何 Mesh。
- 结构基准始终为当前 `Scene Camera`。
- 插件自动收集当前相机画面内、Render 可见的 Mesh，并把真实 3D 几何投影到 `structure_guide.png`。
- 红色对象只额外生成 `product_structure_mask.png` / `product_edit_mask.png`，用于产品局部纠偏；没有红色对象时整个 Camera Structure Lock 仍然有效。

### 2. 修复 Codex 被插件误判“超时”

2.9 及以前对 Codex 长任务使用固定总时长：

- Prompt 润色：240 秒
- 构图验收：180 秒
- ImageGen：420 秒

这些是 `subprocess.run(timeout=...)` 的总墙钟时间，因此 Codex 即使仍在正常处理，也会在到点后被插件强制终止。

2.10 改为可配置：

- Codex 润色：默认 900 秒
- Codex 构图验收：默认 600 秒
- Codex ImageGen：默认 1800 秒
- 任一项设为 `0`：关闭该长任务的插件侧硬超时。

账号/版本检测仍保留短超时，防止无响应进程拖死 Blender。

### 3. 超时报错更明确

超时时明确说明“这是插件侧总时长限制，不代表 OAuth 失效”，并提示用户在 Add-on Preferences 调高或关闭硬超时。

## 保留

- 当前工程独立指定渲染输出目录。
- Codex ChatGPT OAuth。
- Antigravity Google OAuth / Keychain。
- 多参考图、剪贴板粘贴。
- Camera Reference 作为 ImageGen edit base。
- Product Mask 局部结构修复。
- Wondful Compare 工作区。
