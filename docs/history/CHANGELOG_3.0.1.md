# 3.0.1 · Scroll Prompt Editor

## 提示词编辑器

- 提示词区改为固定高度、内部可滚动的编辑区域。
- 标题只显示 `提示词 · N 字`，不再显示行数。
- 删除“展开全文 / 收起”逻辑。
- 不再用长行预览，因此不应出现原先逐行末尾的省略号。
- AI 润色结果仍直接写回唯一的 `props.prompt`，AI 渲染也只读取这一份 canonical prompt。

## Blender 版本适配

- Blender 5.2+：使用官方 `UILayout.textbox` 原生多行文本框，滚动状态由 Blender Region 保存。
- Blender 4.3–5.1：使用一个带原生滚动条的 UIList 兼容编辑区；视觉行采用软换行，但软换行不会被写入真实 Prompt。
- 修复旧兼容编辑器把视觉换行重新拼成真实换行的问题。

## 不变内容

- 3.0 Deterministic Structure Packet 架构不变。
- Camera Base / Product Mask / Depth / Normal / Silhouette / Part ID 逻辑不变。
- Provider、风格刷新、产品 Collection、Compare 等逻辑不变。
