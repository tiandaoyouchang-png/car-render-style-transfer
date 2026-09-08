# Wondful AI 渲染器 3.0.8 测试报告

验证环境：Linux、Python 3.12.13。本轮代码基线为已交付的 3.0.7。

## 已执行

- 20 个插件 Python 模块 AST / py_compile：通过。
- 完整工程全部 Python 文件 AST / py_compile：通过（包括测试与构建 / 冒烟脚本；只编译冒烟脚本，没有执行 Blender）。
- `bl_info.version`、插件名、面板标题、README、changelog、测试报告及验收文档一致性：通过。
- `python3 tools/validate.py` 中的 56 项自动回归：全部通过。

| 回归范围 | 方法与结论 |
| --- | --- |
| Prompt 同步 | Blender Text / Scene 模拟对象；AI 回写不会回退，手改和换行保留，双场景 / 改名隔离，重复打开不清空，关闭 / 卸载前同步 |
| 编辑冲突 | 模拟润色返回期间用户继续编辑；保留手动文本、保存 AI 建议；同时两端更新保留恢复草稿 |
| 编辑 UI | 模拟兼容 textbox、签名不兼容、无 textbox 三条路径；只绑定 canonical Prompt 或整段编辑入口 |
| RNA 声明 | 执行从真实类抽取的 100 个属性声明；均为求值后的 Property 工厂结果，而不是字符串 |
| AGY 登录 | SUCCESS + 无关拒绝通过；认证失败是 LOGGED_OUT；超时 / 403 策略 / 429 / 未知模型是 ERROR；版本失败不阻断探测 |
| CLI 环境 | 保留 PATH / 软链接、无效显式路径、nvm 发现；实际启动模拟 CLI 子进程验证中文、空格路径、同级解释器和关闭 stdin |
| 生图结果 | Provider 响应模拟；不接受输入图或旧候选，支持 fresh output、JSON / stream-json、图像头部检查、缺失参考提前失败 |
| 附件与事件 | AGY 复用 Edit Base；Reference 顺序保留；ACTIVE / DONE 不重复计数 |
| 异步 / 输出 | 线程实测窗口取消后锁仍保留到线程结束、重复清理不释放其他任务锁；模态场景覆盖模拟；提交尺寸快照静态检查 |
| 模式 | 执行实际模式判断表达式；FAST / STANDARD 不启用远程重试，STRICT 保留启用逻辑 |

## 本轮新增 9 项回归

产品默认只识别造型；逐图说明不替换类别边界；环境主参考决定受光且辅助光不互相冲突；无环境图时按文字或中性环境光处理；Structure Packet 与产品 / 人物 / 环境参考编号保持一致；环境独立分析先提取照明；旧 AI 提示词需一次职责迁移刷新；Codex 最终请求携带新规则；AGY 最终请求携带新规则。

测试验证提示词构造、规则传递和刷新条件，不能证明生成模型在每张图上必然遵从。

## 不属于本次通过范围

- 真实 Blender GUI / Runtime 安装注册（提供 `tools/blender_smoke.py`，**待实机执行**）。
- macOS / Windows 上用户真实 PATH、Keychain、OAuth 与 CLI 安装。
- 真实 Codex / AGY 生图、权限策略、模型可用性、画质、结构服从程度。
- EEVEE Depth / Normal / IndexOB、Mask 像素级对齐、复杂模型耗时与 STRICT 纠偏。
- 真实生成速度基准；本版只有重复附件减少和耗时记录，未测得端到端提速比例。
- 位图头部检查只用于拒绝明显非图片，完整图像解码与显示仍需 Blender。

历史测试记录另见 `TEST_REPORT_3.0.7.md`、`TEST_REPORT_3.0.6.md`；当前结论以本文件为准。
