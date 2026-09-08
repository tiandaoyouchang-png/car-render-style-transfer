# Wondful AI 渲染器 2.4

## 本次核心变化

### 1. 独立 Wondful Compare 工作区
- 不再把 AB 对比绘制在 3D Viewport / Camera View 上。
- 当前 Render Session 同时存在 `camera_reference.png` 与 AI 结果时，主面板出现 **进入 Wondful Compare 工作区**。
- 第一次进入时复制当前 Blender Workspace 并建立 `Wondful Compare`；主编辑区域切换为 Image Editor。
- 对比工作区左侧显示 Blender Camera Reference，右侧显示 AI Render；可拖动垂直分割线，也可用侧栏滑块控制分割位置。
- 支持返回进入前的工作区。

### 2. 严格构图锁定
- Camera Reference 从“高优先级参考图”升级为 **源画布 / 原位编辑底图**。
- ImageGen 指令明确要求 image-to-image appearance rerender，而不是重新设计构图。
- 强制约束车辆二维包围框、中心位置、占画面比例、轮心、车头/车尾朝向、相机高度、透视、地平线、遮挡与主体数量。
- 明确禁止 zoom / pan / crop / reframe / 换镜头 / 改焦段观感。

### 3. Codex 构图校验与自动纠偏
- 第一次 ImageGen 完成后，Codex Vision 自动比较 `camera_reference.png` 与候选结果。
- 输出 0-100 构图分数，分别关注车辆位置、尺度、视角、轮心、地平线/透视。
- 默认通过阈值 88 分。
- 低于阈值时，Codex 生成具体纠偏指令，再进行一次 ImageGen；默认最多 2 次，避免无意中过度消耗额度。
- 多个候选中选择构图分数更高的一张作为最终结果。
- 如果构图校验本身不可用，保留第一张高质量结果，不盲目继续消耗 ImageGen。

### 4. 结果记录
- 主面板与 Wondful Compare 侧栏显示构图对齐分数与生成尝试次数。
- `session.json` 新增 alignment score / attempts / threshold / audit 信息。
