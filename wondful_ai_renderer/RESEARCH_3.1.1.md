# Wondful 3.1.1 修复依据与实现取舍

核对日期：2026-09-05。

## 输入超限

用户的 3.1.0 日志明确写明：工具最多支持 5 个参考图路径，本轮提供了 6 张。外层将这个参数错误包装成 OAuth/ImageGen 能力不可用，导致定位方向偏离。

源码中渲染依次追加 Camera Base、全部结构图与外观参考，严格模式还可能增加候选底图与 Mask。修复在提交前整理全部参考，单次最多 5 个独立路径。5 是这次 Codex 运行的已知限制；AGY 也采用同一保守提交预算，不宣称这就是所有 AGY 版本的接口上限。

Camera Base 保持独立完整。其余按结构、产品、人物、环境分组，超限时等比编排；严格模式必要时合并外观组，仍保留每格编号与职责。显式输入清单覆盖原始逻辑编号的路径含义，并禁止追加图集格内的原路径。客户端还有最终容量检查，不自动反复重试参数错误。

图集解决输入数量，并不能保证视觉参考被模型逐像素执行。归一化结构数据和白模底图继续提供约束；原生控制网络不是本版实现范围。

## AGY 登录

3.1.0 每次验证使用新的临时目录；官方交互初始化与验证没有共用工作目录。该实现会妨碍需要工作区确认的 CLI 流程，但未获得用户真实 AGY 日志，不能认定它是本机登录失败的唯一原因。

3.1.1 将官方交互终端登录放到主入口，然后用稳定目录中的新进程验证。macOS 会检查 Terminal 启动结果。保留兼容授权桥接；验证时不会等待用户向无界面进程输入授权码，且所选模型错误和配额错误单独显示。

AGY 官方文档要求 headless 使用缓存凭据，未登录时先完成交互登录。见 [AGY headless 文档](https://www.agy.dev/docs/cli/headless) 与 [安装及认证说明](https://www.agy.dev/docs/cli/install/)。登录凭据仍由官方 CLI 管理，插件没有读取 Keychain 或换取 Token。

## 模型目录与实际选择

Codex 使用 app-server：initialize、initialized、model/list，读取所有分页。不创建 thread 或 turn；选择用于后续 CLI 的 --model 参数。实现依据 [OpenAI 官方 app-server 文档](https://raw.githubusercontent.com/openai/codex/main/codex-rs/app-server/README.md)。

AGY 使用本地 models 子命令读取模型 slug，再传 --model。旧 CLI 不支持时明确报错，不从网页硬编码一份可能与账户不符的列表。命令与失败行为见 [AGY 模型选择说明](https://www.agy.dev/docs/cli/headless)。

模型目录反映 CLI 报告，不等于额度及工具权限验证。界面可选的是推理模型，现有内置生图接口没有实现独立图像模型选择；图像模型未报告时继续记录未知。AGY 的附加图像模型说明见 [官方模型文档](https://www.agy.dev/docs/models/)。

## 长提示词

主面板的 prompt_expanded 属性此前没有被使用。现在实际控制原生文本框高度或旧版回退预览长度。回退预览按中文显示宽度换行，真实多行输入继续使用原有 Text Editor，不建立互相覆盖的逐行 StringProperty 输入框。

预览不会修改 canonical prompt，也不会在用户编辑后用旧预览覆盖内容。400+ 字场景已离线验证；真实 Blender 中文输入法、字号和面板缩放仍需实机检查。

## 保留的内容

3.1.0 Render Director 1.0.0 文件未修改，OpenAI profile SHA-256 与用户日志一致。产品造型/环境打光职责、相机权威、快速/标准单次生图与严格模式修复均保留。基线研究文档 RESEARCH_3.1.0.md 作为历史记录保留。
