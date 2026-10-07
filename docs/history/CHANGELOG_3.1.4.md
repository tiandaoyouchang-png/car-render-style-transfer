# 3.1.4 更新记录

## 目标

3.1.4 不继续扩张 Jev 功能范围，而是把 3.1.3 的语义层收紧成稳定的 Semantic Decision Engine。重点解决并发、安全、回退、缓存、置信度、参考图原子性和 Structure Part-ID 对齐问题。

## P0 修复

- **取消任务不再提前释放全局锁**
  - 用户点击取消后，CLI 子进程会收到终止请求。
  - Jev HTTP 请求无法被系统级强杀时，插件会保持 modal + 全局锁，直到 worker 真正退出。
  - 避免旧任务尚未结束，新任务已经启动造成重复生图、重复扣额度和输出竞争。

- **TypeSafe 凭据不再传给 Codex / Antigravity 子进程**
  - `TYPESAFE_API_KEY`、`TYPESAFE_BASE_URL`、`TYPESAFE_DEFAULT_MODEL` 会从 Agent 子进程环境中剥离。
  - Jev Secret 只供 Wondful 进程内语义客户端使用。

- **Jev 返回值严格校验**
  - System One 响应缺 answer、answer type 不匹配、Choice/Noul/Score 核心字段缺失都会被视为无效。
  - 缺失 Noul 不再默认成 0.5，也不会因为 `>= 0.5` 被误认为身份关键资产。

- **Batch 失败不再 N+1 联网重试**
  - 批量参考图分类失败后整批直接走本地 fallback，不逐张再次访问 Jev。

- **Jev 临时失败不污染长期缓存**
  - 缓存键加入 semantic schema、backend、model。
  - 有 API Key 但 Jev 临时失败产生的 fallback 不写长期缓存；服务恢复后可重新使用 Jev。

- **Fallback 不再擅自指定视觉审美**
  - 删除默认 COMMERCIAL_STUDIO / 全局 Contrast / Global Gloss / Detail 注入。
  - Jev 仅判断 change scope、identity preserve、structural change。
  - 真实视觉风格继续交给参考图 + Codex/AGY Vision。

## 参考图工作流

- **Jev 参考图整理改为异步**
  - 网络请求不再阻塞 Blender UI。
  - UI 明确说明 Jev 只根据文件名和用户备注判断，不读取图片像素。

- **参考图迁移原子化**
  - 原分类先保留容量。
  - 迁移按置信度从高到低接受。
  - 目标分类满 8 张时保留原分类。
  - 提交前验证 input_count == output_count，避免重分类过程中丢图。

## Semantic Part / Material

- **Token matching**
  - 英文对象名先按下划线、连字符、空格和 CamelCase 分词。
  - 避免 `trim` 被 `rim` 命中、`template` 被 `plate` 命中等 substring 误判。

- **材质 fallback 收紧**
  - 不再仅凭 `metallic > 0.7` 就把所有对象判为裸金属。
  - Interior 不再默认等于 Soft Material。
  - Headlamp 不再自动把整套灯总成判为 Optical。

- **低置信材质不进入最终 Prompt**
  - Part 与 Material 使用独立置信阈值。
  - Material confidence 不足时只输出部件角色，不把不可靠材质标签交给生图模型。

- **原始 Object Name 不进入最终 Prompt**
  - 下游使用内部 `PART_###` + Part-ID RGB。
  - 防止第三方模型恶意/异常对象名形成 Prompt Injection。

- **小型身份资产不再因 Part-ID 不可见被完全跳过**
  - 语义状态会检查整个 Product Collection。
  - Part-ID 是否可见变成一个特征，不再作为是否送入语义判断的硬门槛。

## Identity Preserve

- 身份自动保护阈值从 0.5 提高到 0.8。
- 用户明确要求替换 Logo / 车标时，可关闭默认身份保护约束。
- 若判断为几何、相机或构图修改请求，AI 渲染会在 ImageGen 前阻止执行，要求先回 Blender 修改结构。

## Structure Packet

- Standard 模式加入 Part-ID 空间控制。
- Structure Sheet 中保留 `mask / depth / silhouette / part_id` sub-role。
- Codex / AGY 不再使用压缩前的 Reference 编号描述 Structure role，避免 Sheet 合并后的编号错位。

## 自动验证

新增 GitHub Actions：
- Python `compileall`
- 标准库 `unittest` 语义回归

覆盖：
- trim != rim
- template != plate
- missing Noul != true
- fallback 不发明视觉主题
- 明确替换 Logo 时解除默认保护
- 原始对象名不进入下游 Prompt
- 低置信材质不下发
- TypeSafe Secret 不传给 Agent 子进程
- cache key 随 model 变化
