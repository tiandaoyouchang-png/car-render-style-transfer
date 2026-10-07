# 3.1.2 更新记录

## 新增

- **TypeSafe 智能引擎集成**：
  - 引入 `typesafe_engine.py`，使用 TypeSafe System One 语义原语（Choice, Score, Noul）。
  - 参考图角色自动识别与智能分类（Choice 原语：智能判断产品造型、环境风格、人物主体）。
  - 美学参数分析与提示词强化合成（Choice + Score：分析美学主题、光影反差等级、材质高光等级）。
  - 多候选渲染图自动评分优选（Score + Noul：综合结构保真度、光影氛围匹配度、对比度打分，自动选出最优预览图）。
- **任务主动取消**：
  - 增加 `wondful.cancel_task` 算子，在忙碌状态下支持主动取消任务。
  - `cli_transport.py` 增加全局进程跟踪与优雅终止机制，避免长时间阻塞。
- **远程会话追溯**：
  - 渲染及请求过程中记录并提取当前 AI Provider 分配的远程会话 ID（`active_conversation_id`）。
  - 增加 `wondful.copy_conversation_id` 算子，支持面板一键复制终端恢复命令（如 `agy --conversation <id>`）。
- **UI 增强**：
  - 参考图面板增加“TypeSafe 智能分类”操作按钮。
  - 任务执行中提供醒目的“取消当前任务”按钮。
  - 渲染结果中显示 TypeSafe 优选评分与会话追踪信息。

## 兼容性

- 保持与 3.1.1 既有工作流完全兼容。
- 插件声明版本升级为 (3, 1, 2)。
