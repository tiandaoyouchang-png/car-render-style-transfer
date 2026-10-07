# 3.1.5 更新记录

## 目标

3.1.5 专注 Identity Preserve Mask：把 Logo、品牌/车型字标、车牌文字和可读 UI 从“Prompt 保护”升级为实际参与图像编辑的空间保护层。

## 核心实现

- **全分辨率 Part Index**
  - Standard / Strict 模式的原生 Object Index 按最终 Camera Output 分辨率生成。
  - 避免小 Logo / 字标先在低分辨率 Part-ID 中丢失再被放大。
  - FAST 仍保留受限结构分辨率以维持速度。

- **Identity Preserve Mask**
  - Jev / 本地语义判断确认 `LOGO_BADGE / TEXT_BADGE / PLATE / SCREEN_UI` 等身份资产。
  - 通过 Object Index ID 精确提取可见像素。
  - 支持少量像素扩边，默认 2 px。
  - 生成：
    - `identity_preserve_mask.png`：白色为身份保护区；
    - `identity_preserve_mask.npy`：供 worker 组合编辑 Mask；
    - `identity_edit_mask.png`：透明区域可编辑，不透明身份区域保持。

- **真实进入生图链路**
  - 初次生成使用 Camera Base 作为 Edit Base。
  - Identity Edit Mask 作为实际编辑 Mask 传给 Codex / AGY。
  - Prompt 明确声明 Mask 不透明区域不得重绘、改字、改形、改比例或风格化。

- **严格纠偏 + Identity Preserve**
  - 发生构图修复时，纠偏区域与身份保护合并。
  - 只有修复区域内的非身份像素可编辑。
  - Logo / 字标即使落在纠偏范围内也保持不可编辑。

- **AGY 三图上限适配**
  - Identity Mask 预留一个输入槽。
  - 当剩余槽位只有 2 个时，保留独立 Camera Base，并把 Structure / Product / Person / Style 合并为带角色标签的 control bundle。
  - Identity Edit Mask 作为第三个唯一输入，不额外丢失风格/产品职责。
  - 严格纠偏时仍可按既有策略缩减输入集。

- **显式 Logo 替换兼容**
  - 用户明确要求替换 Logo / 车标时，3.1.4 的 preserve decision 会关闭 Identity Preserve Mask。
  - 避免旧 Logo 被保护逻辑锁死。

## 可选硬恢复

新增偏好项：
- `身份资产空间保护`：默认开启。
- `身份保护扩边（像素）`：默认 2。
- `硬恢复身份像素（实验）`：默认关闭。

硬恢复会在最终导出前把 Camera Base 对应的身份区域像素精确回贴。

> 仅当 Camera Base 本身已经包含正确 Logo / 字标外观时建议开启。白模或材质预览不完整时应保持关闭，否则可能把白模像素带回最终结果。

## 一致性

- 开启硬恢复后，Blender 结果预览加载最终导出的恢复后图片，不再显示恢复前候选。
- Metadata 记录 Identity Mask、Mask 路径以及是否执行硬恢复。

## 自动验证

在现有 3.1.4 CI 基础上新增：
- Identity Part-ID 提取测试；
- Mask 扩边测试；
- 无身份资产时自动禁用测试；
- Worker-safe PNG 写入测试。
