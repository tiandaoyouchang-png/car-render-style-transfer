# Wondful AI Renderer 2.15 - UI Recovery

- 修复 2.14 主面板在“提示词”标题后停止绘制的问题。
- 根因：Panel.draw() 内调用 sync_prompt_editor() 修改 CollectionProperty，Blender UI draw 阶段可能禁止 RNA 写入并中止后续绘制。
- Prompt 多行数据改为插件注册和 .blend 文件 load_post 后初始化，Panel.draw() 保持只读。
- 旧工程若尚未初始化 prompt_lines，会显示安全的单行 fallback + “恢复多行编辑”，不会影响参考图、渲染、输出、Structure Lock 和结果区。
- 2.14 的风格参考刷新保护逻辑全部保留。
