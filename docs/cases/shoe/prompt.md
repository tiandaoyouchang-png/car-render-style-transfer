# 案例三：跑鞋 · 城市雨夜 / 运动场晨光

> 本案例的场景图由 Hark 的图像生成工具按插件的提示词结构与参考图分组生成（与单椅案例相同的方法），用于演示插件工作流；不是插件内 Codex / Antigravity Provider 的直接输出。

## 模型与授权

- 模型：Khronos glTF Sample Assets · **MaterialsVariantsShoe** — https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/MaterialsVariantsShoe
- 授权：© 2021 Shopify，CC BY 4.0（https://creativecommons.org/licenses/by/4.0/）
- 署名：Shopify
- 处理：使用 glTF 默认材质变体（浅蓝针织）。
- 环境参考图（refs/）全部由图像生成工具生成，无第三方版权素材。

## Blender 底图

| 底图（材质渲染，作为 Camera Base） | 白模 | Mask |
|---|---|---|
| ![](base.png) | ![](clay.png) | ![](mask.png) |

- Blender 4.3.2（Debian arm64 原生），Cycles CPU 64 spp、无降噪，AgX，960×540，浅灰地面 + 两盏面光（与单椅脚本相同的布光）。
- 机位参数（`tools/render_case.py`）：AZ=45 EL=1.6 TZ=0.4 FILL=0.75（相机在鞋头一侧 3/4 前侧，略俯视；50 mm）。
- Mask：透明背景渲染的 alpha>16 外轮廓填充。

## 提示词（插件里这样填）

### 产品外观（固定，两个场景共用）

```text
【产品外观】浅蓝色针织网面跑鞋，白色发泡中底，深灰色鞋带与鞋口内衬，鞋侧两块半透明灰蓝色 TPU 饰片，后跟提拉环。严格保持图1中鞋子的轮廓、比例、画面位置和视角完全不变，不改鞋型、鞋带走向和饰片形状，不添加 Logo 或文字。
```

## 插件设置

| 项 | 设置 |
|---|---|
| 参考图分组 | 产品造型：不放（颜色/材质以 Blender 材质为准）；人物：不放；环境／风格：每个场景 1 张，作为**主参考**（第一张） |
| 渲染模式 | 标准（Structure Packet：Mask / Depth / Normal / Silhouette） |
| 严格构图锁定 | 开 |
| 结构控制图 | 开 |
| 局部结构修复 | 开 |
| 身份资产空间保护（Identity Preserve） | 关闭也可（鞋面无 Logo；中底的压印字样由底图保留） |
| 生成张数 | 1 |
| 输出 | 16:9，实际 1376×768 |

## 场景：城市街头雨夜（scene_rain.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_rain.png) | ![](scene_rain.png) | ![](checks/scene_rain_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：冷蓝环境光 + 左后方品红/青色霓虹轮廓光、湿地反光和雨丝氛围；不取：画面里的招牌与物体位置。

**环境/风格（每个场景单独填）**

```text
【环境/风格】城市街头雨夜：鞋子站在湿漉漉的黑色柏油路面上，远处积水倒映品红与青色霓虹和暖色路灯，背景大光斑虚化，空中细雨；冷蓝环境光，左后方霓虹轮廓光勾出鞋面边缘。鞋底正下方的路面偏暗，只有一条清晰的深色接触阴影，倒影很淡且不贴着中底，白色中底边缘与路面对比清晰。电影感球鞋广告大片。
English: light-blue knit running sneaker on a wet neon-lit city street at night in the rain; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, ground).

【产品外观】浅蓝色针织网面跑鞋，白色发泡中底，深灰色鞋带与鞋口内衬，鞋侧两块半透明灰蓝色 TPU 饰片，后跟提拉环。严格保持图1中鞋子的轮廓、比例、画面位置和视角完全不变，不改鞋型、鞋带走向和饰片形状，不添加 Logo 或文字。
【环境/风格】城市街头雨夜：鞋子站在湿漉漉的黑色柏油路面上，远处积水倒映品红与青色霓虹和暖色路灯，背景大光斑虚化，空中细雨；冷蓝环境光，左后方霓虹轮廓光勾出鞋面边缘。鞋底正下方的路面偏暗，只有一条清晰的深色接触阴影，倒影很淡且不贴着中底，白色中底边缘与路面对比清晰。电影感球鞋广告大片。
English: light-blue knit running sneaker on a wet neon-lit city street at night in the rain; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the sneaker must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, sole touching the ground at the same place). Only replace the grey studio background and floor with the environment, and relight the shoe to match. Do not crop, zoom, rotate or move the shoe. Keep the sole edge crisp, no bright mirror reflection glued to the sole. Neon signs are abstract light shapes only: no letters, numbers or symbols anywhere. No logos, no watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9: a city street at night in the rain, camera very low near the wet asphalt, slightly looking down. Wet black asphalt with puddles mirroring magenta and cyan neon signs and warm street lamps, shallow depth of field with large bokeh in the background, fine raindrops in the air, cool blue ambient with neon rim light from behind-left. Empty foreground ground area in the center where a product could stand. Cinematic sneaker-commercial look. No people, no shoes, no products, no readable text or letters on signs (abstract glowing shapes only), no watermark.
```
</details>

**采用**：第 2 次（重试）

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 95.9% | >95% |
| 外轮廓 ≤3 px | 79%（≤6 px 88%） | ≥80% |
| 底部偏差 | -4 px | <5 px |
| 内部线条 ≤3 px | 93% | 参考 |
| bbox 偏差 L/R/T | +1 / -2 / +0 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 100% | 参考（不依赖分割） |
| 结论 | ❌ 未达标 | |

> 未达标原因：外轮廓 ≤3 px 为 79%，差 1 个百分点。叠图上鞋形与 Blender 轮廓基本重合，偏差来自深色湿地面与深灰鞋带/后跟颜色接近，GrabCut 在鞋口附近分割不准。另：背景霓虹灯牌里有一个类似“%”的符号（非可读文字）。

- 其他尝试 `attempts/rain_try1.png`：第 1 次：环境段为“路面积水倒映…鞋底与路面接触处有自然接触阴影和倒影，网面上有细小水珠”，倒影贴着中底，GrabCut 把倒影并入鞋底。IoU 94.3%，外轮廓 ≤3 px 70%，底部 -6 px，补充边缘指标 99%，未达标。

## 场景：运动场晨光（scene_track.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_track.png) | ![](scene_track.png) | ![](checks/scene_track_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：右后方低角度金色晨光、长影、薄雾和红色跑道质感；不取：跑道上的物体位置。

**环境/风格（每个场景单独填）**

```text
【环境/风格】运动场晨光：鞋子站在红色塑胶跑道上，白色分道线斜向延伸，右后方低角度金色晨光形成长影子和暖色轮廓光，轻薄晨雾，背景虚化的绿色草坪和看台，淡蓝天空；鞋底与跑道接触处有自然接触阴影。清新有活力的运动品牌广告。
English: light-blue knit running sneaker on a red running track at sunrise with golden rim light; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, ground).

【产品外观】浅蓝色针织网面跑鞋，白色发泡中底，深灰色鞋带与鞋口内衬，鞋侧两块半透明灰蓝色 TPU 饰片，后跟提拉环。严格保持图1中鞋子的轮廓、比例、画面位置和视角完全不变，不改鞋型、鞋带走向和饰片形状，不添加 Logo 或文字。
【环境/风格】运动场晨光：鞋子站在红色塑胶跑道上，白色分道线斜向延伸，右后方低角度金色晨光形成长影子和暖色轮廓光，轻薄晨雾，背景虚化的绿色草坪和看台，淡蓝天空；鞋底与跑道接触处有自然接触阴影。清新有活力的运动品牌广告。
English: light-blue knit running sneaker on a red running track at sunrise with golden rim light; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the sneaker must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, sole touching the ground at the same place). Only replace the grey studio background and floor with the environment, and relight the shoe to match. Do not crop, zoom, rotate or move the shoe. No text, no numbers, no logos, no watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9: an outdoor athletics running track at sunrise, camera very low just above the red rubber track surface, slightly looking down. Crisp white lane lines receding diagonally, soft golden low sun from back-right creating long shadows and warm rim light, light morning haze, blurred green infield and stadium seats in background, clear pale blue sky. Empty foreground area in the center where a product could stand. Fresh, energetic sports-brand campaign look. No people, no shoes, no products, no text, no numbers on the track, no watermark.
```
</details>

**采用**：第 1 次

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 97.9% | >95% |
| 外轮廓 ≤3 px | 94%（≤6 px 98%） | ≥80% |
| 底部偏差 | +0 px | <5 px |
| 内部线条 ≤3 px | 85% | 参考 |
| bbox 偏差 L/R/T | -9 / -2 / -1 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 99% | 参考（不依赖分割） |
| 结论 | ✅ 达标 | |

> 中底上的压印字样来自模型贴图，生成后保留。


