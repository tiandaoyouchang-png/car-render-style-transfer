# Wondful AI Renderer · Blender AI 渲染器

> 在 Blender 里打好一个机位，一键生成多张商业级场景大片，**产品的轮廓、比例和位置不跑偏**。

![YU7 四场景](docs/showcase/yu7_grass.jpg)

Wondful AI Renderer 是一个开源的 Blender 插件。它把 Blender 当作“构图与结构的唯一真相”：先从你的相机渲出白模底图和结构图（Depth / Normal / 部件 ID），再调用本机已登录的 **Codex CLI** 或 **Antigravity CLI** 生图，最后按结构做验收和纠偏。适合汽车、家具、家电、鞋包等任何有 3D 模型的产品。

English: an open-source Blender add-on that turns one camera setup into multiple photoreal commercial scenes with AI, while keeping the product's silhouette, scale and position locked to the Blender render. Works with any product that has a 3D model.

---

## 效果展示

### 案例一：小米 YU7 · 一个底图，四种户外场景

| Blender 白模 | 雪坡 | 草地 |
|---|---|---|
| ![](docs/showcase/yu7_clay.jpg) | ![](docs/showcase/yu7_snow.jpg) | ![](docs/showcase/yu7_grass.jpg) |
| **沙漠** | **泥地** | |
| ![](docs/showcase/yu7_sand.jpg) | ![](docs/showcase/yu7_mud.jpg) | |

同一个 3/4 前侧低机位。以 Blender 底图为基准做轮廓检测：

| 场景 | 轮廓 IoU | 外轮廓 ≤3 px | 底部偏差 |
|---|---|---|---|
| 雪坡 | 96.8% | 84% | 0 px |
| 草地 | 97.2% | 88% | +2 px |
| 沙漠 | 96.7% | 86% | +4 px |
| 泥地 | 96.2% | 86% | +1 px |

### 案例二：设计单椅 · 四种家居风格

| Blender 白模 | Blender 底图 | 北欧客厅 |
|---|---|---|
| ![](docs/showcase/chair_clay.jpg) | ![](docs/showcase/chair_base.jpg) | ![](docs/showcase/chair_nordic.jpg) |
| **侘寂茶室** | **工业 Loft** | **地中海露台** |
| ![](docs/showcase/chair_wabi.jpg) | ![](docs/showcase/chair_loft.jpg) | ![](docs/showcase/chair_terrace.jpg) |

| 场景 | 轮廓 IoU | 外轮廓 ≤3 px | 底部偏差 |
|---|---|---|---|
| 北欧客厅 | 99.2% | 100% | 0 px |
| 侘寂茶室 | 97.9% | 92% | 0 px |
| 工业 Loft | 99.0% | 99% | +1 px |
| 地中海露台 | 98.4% | 99% | 0 px |

> 指标用 GrabCut 分割生成图中的产品，再与 Blender 渲染的产品 Mask 对比，属于近似测量。

---

### 更多案例：球鞋 · 腕表 · 复古相机 · 台灯

每个案例的**完整提示词（产品外观 + 环境/风格）、参考图、插件参数和逐张轮廓数据**见 [docs/CASES.md](docs/CASES.md)，单独的提示词文件在 `docs/cases/<案例>/prompt.md`。数据如实标注，未达标的场景也写明了原因。

| 跑鞋 · 运动场晨光 | 跑鞋 · 城市雨夜 | 腕表 · 黑色大理石 |
|---|---|---|
| ![](docs/showcase/shoe_track.jpg) | ![](docs/showcase/shoe_rain.jpg) | ![](docs/showcase/watch_marble.jpg) |
| **腕表 · 岩石登山** | **台灯 · 咖啡馆** | **台灯 · 极简卧室** |
| ![](docs/showcase/watch_rock.jpg) | ![](docs/showcase/lamp_cafe.jpg) | ![](docs/showcase/lamp_bedroom.jpg) |
| **复古相机 · 街头胶片** | **复古相机 · 复古书房** | |
| ![](docs/showcase/camera_street.jpg) | ![](docs/showcase/camera_study.jpg) | |

模型均来自 [Khronos glTF Sample Assets](https://github.com/KhronosGroup/glTF-Sample-Assets)：MaterialsVariantsShoe（© 2021 Shopify, CC BY 4.0）、ChronographWatch（© 2025 Darmstadt Graphics Group, CC BY 4.0，表盘 Logo 为商标）、AntiqueCamera（© 2018 UX3D, CC0）、IridescenceLamp（© 2022 Wayfair, CC BY 4.0）。参考图均为 AI 生成。

## 核心能力

- **白模相机即构图权威**：输出与 Blender Camera 完全同机位；比例不一致时等比缩放、透明留边，不裁切、不拉伸。
- **结构图约束**：自动渲出 Camera Base、Depth、Normal、部件 ID（Object Index），作为生图的结构参考。
- **Identity Preserve Mask**：按部件锁定产品身份区域（车标、灯组、轮毂、Logo 等），只放开环境、光影与材质质感。
- **严格模式验收 + 纠偏**：每张候选图按比例、位置、轮廓检查，不合格自动用 Mask 局部修复重试。
- **双 Provider**：Codex 每次独立生成 4 张，Antigravity 每次 2 张；模型列表来自本机官方 CLI，不做跨模型静默回退。
- **参考图管理**：产品参考决定身份造型，环境参考决定受光、反射和氛围；超出容量的参考自动整理成带编号的图集。
- **AI 润色提示词**：给参考图即可，AI 先分析环境的主光、色温和氛围（结果可编辑），再写成完整提示词；也可输入中文创意需求一键扩写。
- **产品外观锁定**（3.1.7）：配色与材质默认读取 Blender 材质；锁定的产品质感与“必须保留的细节”原样进入每个场景，换环境只重写环境与光影。
- **Compare 对比视图**：底图与结果叠加对比，所有候选图写入输出目录。

## 工作原理

```text
Blender 场景 + 相机 + 产品集合
        │
        ▼
 Camera Base（白模） + Depth / Normal / Part ID
        │
        ▼
 提示词（AI 润色）+ 产品参考 + 环境参考
        │
        ▼
 Codex CLI / Antigravity CLI 生图（本机登录）
        │
        ▼
 比例适配 → 结构验收 → Identity Mask 纠偏（严格模式）
        │
        ▼
 输出目录 + Blender 内预览 / Compare
```

## 环境要求

- Blender **4.3 及以上**
- 本机安装并登录以下任一官方 CLI：
  - [Codex CLI](https://github.com/openai/codex)（需要具备图像生成能力的账号）
  - Antigravity CLI（Google 账号登录）
- 可选：`TYPESAFE_API_KEY`（Jev 语义引擎，无 Key 时自动使用本地规则）

## 安装

1. 下载仓库，将 `wondful_ai_renderer/` 文件夹打成 ZIP（或使用 Releases 中的安装包）。
2. Blender → 编辑 → 偏好设置 → 插件 → 从磁盘安装 → 选择 ZIP → 启用。
3. 在 3D 视图侧边栏（N 面板）找到 **Wondful AI 渲染器**，确认面板显示的版本号。

## 快速上手

1. 把产品放进一个集合，设置好相机（建议 3/4 前侧、略低机位）。
2. 按面板四步走：
   - ① 连接：Codex 点「使用 ChatGPT 登录」；Antigravity 点「Google 登录」后再点「验证登录」。
   - ② 产品：选产品集合，放一张产品三视图（正/侧/后拼成一张）。
   - ③ 场景：放环境参考图（第一张决定主光），可写一句需求，例如“雪地清晨，冷色调”。
   - ④ 点「生成」：自动读产品图、分析环境、写提示词，再渲染并验收轮廓。
3. 在结果区看最佳图，点「对比」和底图对照，或「再来一张」；所有候选图都在输出目录。
4. 想手动调整时展开「高级」：模型选择、提示词全文、产品外观锁定、环境分析、渲染模式、输出目录都在这里；打开「分两步」可以先看提示词再渲染。

## 开发与测试

```bash
# 离线测试
python -m unittest discover -s tests -p "test_*.py" -v

# Blender 实机验收（无 GPU 可用 Cycles 代替 EEVEE 渲染结构图）
WONDFUL_STRUCTURE_ENGINE=CYCLES blender -b --factory-startup \
  --python tools/blender_acceptance.py -- --out /tmp/wondful_accept
```

## 仓库结构

```text
wondful_ai_renderer/       Blender 插件主体
skills/                    汽车渲染风格迁移技能包（可给 Codex 等 Agent 使用）
geometry-render-pipeline/  几何约束商业渲染管线 V0.1 原型
tests/                     离线测试
docs/showcase/             README 展示图
```

## 已知限制

- 结构图以参考图形式交给 CLI 的生图工具，不是原生 ControlNet，无法保证像素级对齐；严格模式的验收与 Mask 纠偏用来兜底。
- 实际出图质量取决于 CLI 背后的图像模型与账号额度；严格模式的远程调用次数可能多于最终导出张数。
- Blender 5.x 的合成器 API 有较大变化，自 3.1.6 起已适配（实测 Blender 5.1.2）。

## 致谢

- 小米 YU7 模型：Sketchfab，作者 Ddiaz Design（展示用途）
- 单椅模型：Khronos glTF Sample Assets · SheenChair，© 2020 Wayfair LLC，CC0 1.0

## 参与贡献

欢迎提 Issue 和 PR：新场景预设、更多 Provider、更好的验收算法、其他品类的案例都非常欢迎。觉得有用请点个 ⭐ Star。

## License

[MIT](LICENSE)
