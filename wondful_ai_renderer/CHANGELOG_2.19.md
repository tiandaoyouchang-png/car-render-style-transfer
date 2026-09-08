# CHANGELOG 2.19 · Product Collection Lock

## Structure Lock

- 新增 Scene 级 `产品集合` Collection picker。
- Scene Camera 仅作为全画面 Composition / Camera 基准。
- 产品集合及其子集合的可见 Mesh 是唯一产品结构来源。
- Structure Guide / Product Mask 不再扫描全场景 Mesh。
- 移除红色材质作为 Structure Lock 产品识别条件。
- 未选择产品集合时不再回退全场景；主面板明确提示并阻止严格结构渲染。
- `structure_control.json` 新增 `product_collection_name` / `product_collection_mesh_count`。
- Codex/Antigravity 结构提示同步更新为 Product Collection 语义。

## 保留

- 2.18 风格参考刷新与 SHA-256 防旧缓存机制。
- 2.17 单一 Prompt 编辑器与按钮内进度。
- Camera Reference 仍然每次 AI Render 重新捕获当前最新 Scene Camera。
