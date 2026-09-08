# 3.0 · Deterministic Structure Packet

## 核心架构

Wondful 3.0 将构图控制从“Camera Screenshot + Prompt 强调”重构为：

**Deterministic Geometry → Structure Packet → Generative Appearance**

Blender 负责 Structure，AI 只负责 Appearance。

## Structure Packet

每次 AI 渲染会在独立 Render Session 中自动生成：

- `01_camera_base.png`：Blender Scene Camera 原位编辑底图，最高结构优先级。
- `02_product_mask.png`：所选产品 Collection 的可见 footprint。
- `03_scene_depth.png`：Scene Camera 深度层级，近白远黑。
- `04_scene_normal.png`：可见表面法线/曲面朝向。
- `05_product_silhouette.png`：产品可见外轮廓。
- `06_part_id.png`：产品 Collection 内 Mesh 对象的确定性部件分区色。
- `07_structure.json`：Camera、分辨率、bbox、center、wheel anchors、Part-ID 映射与文件职责。

## 原生数据 Pass

- 优先在隔离的临时 Blender Scene 中用 EEVEE Next 生成 Depth / Normal / Object Index。
- 不修改用户 Scene 的 Render Engine、Compositor、Resolution、View Layer Pass 设置。
- 对产品 Mesh 临时分配 `pass_index`，任务结束后恢复。
- 如果当前 Blender/场景无法输出原生数据 Pass，自动回退到 2.x 的投影结构控制，不中断整个插件。

## 渲染模式

- 快速预览：Camera Base + Product Mask / Silhouette。
- 标准：Camera Base + Mask + Depth + Normal + Silhouette；单次生图。
- 严格对齐：完整 Structure Packet（额外 Part ID）+ 远程验收/局部修复。

## 结构与外观职责

- Camera Base：Camera / Composition / Perspective / whole-frame spatial relationship。
- Product Mask：产品 Position / Scale / visible footprint。
- Scene Depth：前中后景深度与遮挡层级。
- Scene Normal：曲面朝向、车身曲率、表面结构。
- Product Silhouette：产品外轮廓。
- Part ID：Mesh 语义分区，不是最终颜色。
- Product / Person / Style Reference：只控制身份或视觉外观，不允许覆盖 Blender 结构。

## UI

- `Camera Structure Lock` 改为 `Blender Structure Lock`。
- 相机名 + 输出分辨率继续集中显示在 Structure Lock 内。
- 产品 Collection 仍是唯一产品结构来源。
- 结构图全部后台自动生成，不要求用户手工管理。

## 兼容与限制

- Codex / Antigravity 当前仍通过其通用多图编辑/生图能力接收 Structure Packet；并非专用 ControlNet API。
- 因此 3.0 显著强化了结构条件与可诊断性，但不能承诺生成模型达到数学意义上的逐像素硬锁。
- 真正的 ControlNet / Depth-Control 专用后端可以在 3.x 的 Provider Adapter 上继续接入。
