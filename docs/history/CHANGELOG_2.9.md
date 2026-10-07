# Wondful AI 渲染器 2.9 · Antigravity OAuth

## 1. Google 分析引擎迁移到 Antigravity CLI

- 移除个人账号工作流中的旧 `Gemini CLI` 客户端。
- Google 分析引擎改为官方 **Antigravity CLI (`agy`)**。
- 分析引擎选择改为：`Codex` / `Antigravity`。
- Antigravity 负责：Camera / Structure Guide / Mask / 产品、人物、风格参考图的视觉分析、AI 润色、生成后构图验收。
- 最终生图仍由 Codex ImageGen 执行，避免更换已经稳定的商业渲染链路。

## 2. Google Auth 不使用 API Key

- 插件不读取、不复制、不保存 Google OAuth Token。
- `agy` 优先复用系统原生 Keychain / Credential Manager 中的缓存登录。
- 未登录时，插件的“Google 登录”按钮只负责在系统 Terminal 启动 `agy`；浏览器登录与 Token 生命周期由 Antigravity CLI 自身管理。
- “检测”按钮使用一次无工具的 Headless 请求验证当前缓存登录是否真的可用。

## 3. Headless 调用切换到 `agy`

插件后台使用官方 Headless 形态：

```text
agy --output-format json --print-timeout <N>s --prompt "..."
```

若用户在偏好设置指定模型，则额外传入：

```text
--model <model-slug>
```

Blender 参考图会先复制进当前 Render Session 的 `antigravity_inputs/` 目录，再由 Antigravity 在工作区内读取。插件不使用 `--dangerously-skip-permissions`；Wondful 只需要工作区图片读取权限。

## 4. 多模态 Reference 语义保持不变

Antigravity 与 Codex 共享相同参考优先级：

1. Camera Reference：构图 / Camera / 空间关系
2. Structure Guide / Product Mask：车辆或产品几何位置与轮廓约束
3. Product References：产品身份与真实外观
4. Person References：人物身份
5. Style References：视觉风格

Google 分析引擎切换不会改变 2.8 的 Structure Lock 原则。

## 5. 2.8 能力全部保留

- 当前 `.blend` 可独立指定最终渲染输出目录。
- Camera Reference 作为首轮 Base Image Edit。
- Blender evaluated Mesh 相机投影生成 Structure Guide / Product Mask。
- 构图验收读取 bbox / center / wheel anchors。
- 低分时使用上一轮结果 + 产品局部 Mask 做结构修复。
- 独立 Wondful Compare Workspace。
- 多参考图缩略图卡片、排序、替换、删除与剪贴板粘贴。

## 客观限制

- Antigravity 在 2.9 中只做“视觉理解 / AI 润色 / 构图验收”，不承担最终 AI 生图。
- Headless 模式依赖本机 `agy` 版本与 Google 账号可用状态；真实 OAuth/Keychain 行为需要在用户机器实测。
- 最终图像几何服从程度仍受当前 Codex ImageGen / Image Edit 工具能力约束。
