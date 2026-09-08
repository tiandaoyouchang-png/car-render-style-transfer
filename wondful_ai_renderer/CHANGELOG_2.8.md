# Wondful AI 渲染器 2.8 · Structure Lock

## 1. 当前工程可明确指定渲染输出位置

- 主面板“渲染输出”增加独立 **选择** 按钮，直接调用 Blender 文件夹选择器。
- 选择结果保存到当前 Scene 的 `output_directory`，随 `.blend` 工程保存；不同工程可以使用不同输出目录。
- 当前工程未指定时，才回退到插件全局输出目录；两者都为空时：已保存工程使用 `//Wondful_Renders/`，未保存工程使用 `~/Pictures/Wondful_AI_Renderer/`。
- “打开输出目录”与结果卡片均使用当前实际输出目录。
- 最终导出仍使用 Scene + Camera + Session 命名并避免覆盖旧文件。

## 2. Structure Lock：从 Prompt 约束升级为 Blender 几何约束

原 2.7 的自动纠偏仍然主要依赖“参考图 + Prompt + 生成后评分”。2.8 增加 Blender 侧结构控制数据：

- `camera_reference.png`：Scene Camera 原始构图基准。
- `structure_guide.png`：从真实 Blender Mesh 按当前 Scene Camera 精确投影的线框 / 中心 / 轮心 Anchor Guide。
- `product_structure_mask.png`：真实投影产品 footprint。
- `product_edit_mask.png`：用于二次局部修复的轻微膨胀产品编辑区域。
- `structure_control.json`：归一化产品 bbox、中心和可识别轮心锚点。

结构对象来源：

1. 用户在主面板点击 **锁定当前选中**，显式指定车辆 / 产品 Mesh；
2. 未指定时自动检测红色产品对象；
3. 两者都没有时保持兼容并退回 Camera Reference 模式。

## 3. Mask 精度升级

- 不再用简单凸包作为主要产品 Mask。
- 优先把 evaluated Mesh 的三角面逐个投影到当前 Camera，栅格化成真实产品屏幕 footprint。
- 凸包仅作为异常 Mesh 无法三角化时的降级路径。
- 局部编辑 Mask 基于真实投影 footprint 做小幅 dilation，为轮胎、保险杠等边缘修复保留必要空间，但不开放整张图重构。

## 4. 首轮生成改为 Base Image Edit

- 首轮不再只把 Camera Reference 当普通参考图。
- Codex ImageGen 任务明确要求将 `camera_reference.png` 作为 **edit base / source canvas**，在同一画布上做 Appearance rerender。
- 允许更新材质、灯光、反射、环境与商业摄影质感，但 Camera / Geometry / Position / Scale / Rotation / Perspective 必须服从 Blender。
- Camera Reference 始终保持附件 Reference 1，结构图 / Mask 位于后续固定位置，避免修复轮次附件顺序改变导致 Reference 编号错位。

## 5. 二次纠偏改为局部 Image Edit

当构图评分低于阈值时：

- 以上一轮高质量结果作为 edit base；
- 使用 Blender 生成的 `product_edit_mask.png` 作为局部编辑约束；
- 优先只修复车辆位置、尺度、视角、轮廓和轮心；
- 尽量保留已经满意的材质、灯光、背景与后期。

如果当前 Codex ImageGen tool schema 暴露 `input_image_mask / mask`，任务会明确要求使用；如果未暴露，则把 Mask 作为视觉区域约束降级使用。

## 6. 构图验收加入 Blender 数值锚点

Codex / Gemini 构图验收除 Camera Reference 外，还可读取 `structure_guide.png` 与：

- `target_bbox`
- `target_center`
- `target_wheel_anchors`

纠偏要求尽量输出画宽 / 画高百分比，例如“车辆中心向右移动约 2.5% 画宽、整体缩小约 4%”。这比“更接近参考图”一类泛化指令更适合下一次局部编辑。

## 客观限制

Structure Lock 能显著减少生成模型自由重构构图的空间，但 Codex 当前暴露的 ImageGen 是否支持显式 Mask、以及其 Mask / high-fidelity edit 的实际服从程度仍由当前 runtime / 账号 / image tool 决定。2.8 不宣称传统 3D 渲染器级逐像素几何锁定；若工具不暴露硬结构控制接口，结构图仍属于多模态视觉约束。
