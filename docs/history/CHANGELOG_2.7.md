# Wondful AI 渲染器 2.7

## 新增：可选渲染输出目录

- 主面板增加“渲染输出”目录设置。
- 可直接使用 Blender 的文件夹选择器指定最终 AI 渲染图保存位置。
- 留空时：已保存 `.blend` 默认输出到工程目录下 `Wondful_Renders/`；未保存工程默认输出到 `~/Pictures/Wondful_AI_Renderer/`。
- AI Render 完成后，会把最终比例校正后的图片复制到该目录。
- 文件名包含 Scene、Camera 与 Render Session，重复时自动追加序号，避免覆盖。
- 最新结果卡片显示实际导出路径，并增加“打开输出目录”。
- Render Session 缓存仍保留在 `~/.wondful_ai_renderer/cache/`，不与用户导出目录混用。

## 修复：Wondful Compare 鼠标拖动

- 修复从 Image Editor 侧栏启动 Modal 时，事件区域绑定在 UI Region、导致画面内拖动不可用的问题。
- Compare 工作区打开后自动尝试从 Image Editor 的 `WINDOW` Region 启动鼠标拖动。
- 即使自动启动失败，右侧仍可点击“启用鼠标拖动”。
- 鼠标坐标改用 Blender 全局窗口坐标 + Image Editor WINDOW Region 计算，不再依赖 Sidebar 的 `mouse_region_x`。
- 对 View All 后的实际图片显示矩形进行宽高比校正，因此横版/竖版图片均能把鼠标 X 正确映射为分割位置。
- 只在图片范围内按住左键时开始拖动，避免影响右侧 UI。
- 拖动模式失效或用户主动退出时，右侧“分割位置”滑块仍作为永久兜底。
- 进入其他 Workspace 时自动结束 Compare Modal，避免残留事件处理器。
