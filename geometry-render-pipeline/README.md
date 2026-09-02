# Geometry-Conditioned Commercial Render Pipeline

这是一个可运行的 V0.1 工程，包含两部分：

- `blender-extension/ai_commercial_render/`：Blender 扩展，负责 Geometry Truth、Camera、六类控制图、任务打包和 GPT Image 2 调用。
- `codex-plugin/`：Codex 插件，负责读取 Blender Job，或从单张白模图进入同一套汽车/产品商业渲染流程。

## 架构

```text
Blender Mesh + Camera + Material Classes
                │
                ▼
       Deterministic Eevee Passes
                │
 ┌────────┬────────┬───────┬──────┬─────────────┬──────┐
 │ Clay   │ Normal │ Depth │ Edge │ Material ID │ Mask │
 └────────┴────────┴───────┴──────┴─────────────┴──────┘
                │
                ▼
         Reproducible Job Folder
(camera + model revision + prompt + ordered image roles)
                │
        ┌───────┴─────────┐
        ▼                 ▼
 Blender direct API    Codex workflow
        │                 │
        └───────┬─────────┘
                ▼
       OpenAI Image Edit API
                │
                ▼
       Commercial Render Output
```

## 设计边界

- Blender / Three.js 类传统图形管线负责准确几何、相机投影、轮廓、深度和材质区域。
- GPT Image 负责 CMF、灯光、反射、环境、氛围和商业摄影完成度。
- Codex 登录负责 Codex 会话；直接图像 API 请求使用独立的 OpenAI Platform 项目 API Key。

## V0.1 功能

- 选中对象、Collection 或可见场景范围。
- 自动/手动分类车漆、玻璃、轮胎、轮毂、刹车、灯具、金属、黑塑料、内饰和发光材质。
- 导出 Clay / Normal / Depth / Edge / Material ID / Mask。
- 保存相机位置、四元数、投影、FOV、裁切、分辨率、模型 revision 和边界框。
- 支持材质、灯光和环境三种参考图，并严格隔离参考职责。
- 直接调用 `gpt-image-2` 的 Image Edit API。
- 导出自包含 Job，内含 `AGENTS.md` 和无依赖生成脚本，可在 Codex 中运行。
- API 请求在后台线程执行，不阻塞 Blender UI；控制图导出仍在 Blender 主线程执行。

## 尚未包含

- 多机位批量 Job。
- 生成图对原始投影的自动边缘/关键点相似度验收。
- 面向车型部件的实例分割与更精细 Material-ID 训练。
- Blender 内部结果 A/B 评测面板。

这些结构已在 Job schema 中预留扩展空间。
