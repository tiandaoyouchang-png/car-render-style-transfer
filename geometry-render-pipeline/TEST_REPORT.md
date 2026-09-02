# Geometry-Conditioned Commercial Render Pipeline — Test Report

**版本：** 0.1.0  
**测试日期：** 2026-09-02  
**测试环境：** Linux x86_64，Python 3.13.5；当前执行环境未安装 Blender 可执行程序。

## 已通过的自动测试

执行命令：

```bash
python3 -m compileall -q blender-extension codex-plugin tests
python3 -m unittest discover -s tests -v
bash -n codex-plugin/install-personal.sh
python3 /home/oai/skills/skill-creator/scripts/quick_validate.py \
  codex-plugin/skills/commercial-render-director
```

通过 11 项测试：

1. Blender 包可在模拟 `bpy` API 下完成模块导入与注册入口发现。
2. Prompt Compiler 强制写入汽车几何锁、Material-ID 图例和单图输出要求。
3. Multipart 请求对每张输入图重复使用 `image[]` 字段。
4. Blender API 客户端对本地模拟 HTTP 服务完成端到端请求、解码和 request ID 读取。
5. Codex 单白模 CLI 对本地模拟 Image API 完成端到端生成并写入元数据。
6. Blender Job 自带生成脚本对本地模拟 Image API 完成端到端生成。
7. Blender Extension Manifest 与 Codex Plugin Manifest 结构检查通过。
8. 中英文汽车材质命名自动分类测试通过。
9. 两个命令行生成脚本的 `--help` 和参数解析通过。
10. Codex 个人 Marketplace 安装器可保留已有插件并正确加入本插件。
11. 全目录未发现疑似硬编码 OpenAI API Key。

Codex Skill 已通过 `quick_validate.py`。

## 尚未在当前环境完成的测试

### Blender 4.2+ 真实运行测试

当前容器没有 Blender，且无法在此环境取得 Blender 二进制，因此没有实际执行 Eevee 渲染、节点创建和六通道图片导出。源码内已提供：

```bash
blender --background --factory-startup --python tests/blender_smoke_test.py
```

该脚本用于本机真实验证 Clay、Normal、Depth、Edge、Material ID 和 Mask 六张图。

### OpenAI 线上 Image API 测试

没有使用或要求用户提供 API Key，因此没有产生真实计费请求。网络层、multipart 请求、base64 响应解码和文件写入均使用本地模拟服务验证。

## 结论

当前版本属于**结构完整、静态与本地集成测试通过的可安装 V0.1**。在标记为 Blender 生产可用之前，仍应在目标 Mac 与实际 Blender 版本中完成一次真实冒烟测试，并使用一个真实汽车白模 Job 完成首次 GPT Image 2 请求。
