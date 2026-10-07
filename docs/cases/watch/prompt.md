# 案例四：计时腕表 · 黑色大理石微距 / 户外岩石登山

> 本案例的场景图由 Hark 的图像生成工具按插件的提示词结构与参考图分组生成（与单椅案例相同的方法），用于演示插件工作流；不是插件内 Codex / Antigravity Provider 的直接输出。

## 模型与授权

- 模型：Khronos glTF Sample Assets · **ChronographWatch** — https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/ChronographWatch
- 授权：© 2025 Darmstadt Graphics Group GmbH，CC BY 4.0；模型与贴图 Eric Chadwick，源自 Sketchfab “Chronograph Watch Mudmaster”（graphiccompressor，CC BY 4.0）。表盘上的 Khronos / 3D Commerce / DGG 标志为各自商标，不在 CC BY 授权范围内
- 署名：Eric Chadwick / DGG（源模型 graphiccompressor）
- 处理：Blender 4.3.2 自带 glTF 导入器在该模型的 KHR_materials_variants 上报错（TypeError），所以先把 “Midnight Gold” 变体烘成默认材质、去掉 variants 扩展后再导入（几何不变）。
- 环境参考图（refs/）全部由图像生成工具生成，无第三方版权素材。

## Blender 底图

| 底图（材质渲染，作为 Camera Base） | 白模 | Mask |
|---|---|---|
| ![](base.png) | ![](clay.png) | ![](mask.png) |

- Blender 4.3.2（Debian arm64 原生），Cycles CPU 64 spp、无降噪，AgX，960×540，浅灰地面 + 两盏面光（与单椅脚本相同的布光）。
- 机位参数（`tools/render_case.py`）：AZ=-25 EL=0.7 FILL=0.8（表盘朝前、3/4 左前方，略俯视；50 mm）。
- Mask：透明背景渲染的 alpha>16 外轮廓填充。

## 提示词（插件里这样填）

### 产品外观（固定，两个场景共用）

```text
【产品外观】香槟金色金属表壳的多功能计时腕表，八角形表圈带银色螺丝和按键，黑色表盘、金色大号数字 12/3/6/9 与指针、下方液晶小窗，金色菱格纹表带与灰色塑料部件。严格保持图1中腕表的轮廓、比例、画面位置和视角完全不变，表盘指针位置与大号数字不变，不新增文字或 Logo。
```

## 插件设置

| 项 | 设置 |
|---|---|
| 参考图分组 | 产品造型：不放（颜色/材质以 Blender 材质为准）；人物：不放；环境／风格：每个场景 1 张，作为**主参考**（第一张） |
| 渲染模式 | 标准（Structure Packet：Mask / Depth / Normal / Silhouette） |
| 严格构图锁定 | 开 |
| 结构控制图 | 开 |
| 局部结构修复 | 开 |
| 身份资产空间保护（Identity Preserve） | 开启（表盘有字标/Logo），扩边 2 px；硬恢复关闭 |
| 生成张数 | 1 |
| 输出 | 16:9，实际 1376×768 |

## 场景：黑色大理石微距（scene_marble.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_marble.png) | ![](scene_marble.png) | ![](checks/scene_marble_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：低调棚拍——左上窄长柔光条形成的长条高光、右侧暖金点缀光、深黑背景、抛光石面倒影；不取：石纹的具体走向。

**环境/风格（每个场景单独填）**

```text
【环境/风格】黑色大理石微距：腕表站在抛光的黑色大理石台面上，石面有白色与淡金色细纹理，左上方一条窄长柔光箱在金属表壳和台面上形成长条高光，右侧微弱暖金色点缀光，背景沉入深黑，台面有腕表的清晰倒影。低调奢华腕表广告大片，微距质感。
English: champagne-gold chronograph watch standing on polished black marble, low-key luxury macro lighting; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, surface).

【产品外观】香槟金色金属表壳的多功能计时腕表，八角形表圈带银色螺丝和按键，黑色表盘、金色大号数字 12/3/6/9 与指针、下方液晶小窗，金色菱格纹表带与灰色塑料部件。严格保持图1中腕表的轮廓、比例、画面位置和视角完全不变，表盘指针位置与大号数字不变，不新增文字或 Logo。
【环境/风格】黑色大理石微距：腕表站在抛光的黑色大理石台面上，石面有白色与淡金色细纹理，左上方一条窄长柔光箱在金属表壳和台面上形成长条高光，右侧微弱暖金色点缀光，背景沉入深黑，台面有腕表的清晰倒影。低调奢华腕表广告大片，微距质感。
English: champagne-gold chronograph watch standing on polished black marble, low-key luxury macro lighting; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the watch must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, touching the surface at the same place). Only replace the grey studio background and floor with the environment, and relight the watch to match. Do not crop, zoom, rotate or move the watch. Keep the dial layout; do not invent new text. No watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9, macro luxury still-life set: a polished black Nero Marquina marble surface with fine white and subtle gold veins, camera low and close to the surface. Low-key studio lighting: one narrow softbox strip from upper left creating a long specular streak on the marble, deep black background falling into darkness, a faint warm gold accent light from the right. Glossy reflections on the marble. Empty center area where a product could stand. High-end watch advertising mood. No products, no watches, no text, no watermark.
```
</details>

**采用**：第 1 次

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 97.8% | >95% |
| 外轮廓 ≤3 px | 84%（≤6 px 86%） | ≥80% |
| 底部偏差 | +0 px | <5 px |
| 内部线条 ≤3 px | 89% | 参考 |
| bbox 偏差 L/R/T | +0 / -1 / -1 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 91% | 参考（不依赖分割） |
| 结论 | ✅ 达标 | |

> 表盘上的城市缩写、3D Commerce 字标等微小文字在 1376 px 输出中有轻微变形（底图本身也很小）；大号数字与指针保持正确。


## 场景：户外岩石登山（scene_rock.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_rock.png) | ![](scene_rock.png) | ![](checks/scene_rock_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：左侧傍晚金色阳光、清晰硬阴影、花岗岩质感和远山虚化；不取：登山绳的位置（要求放在画面最右侧）。

**环境/风格（每个场景单独填）**

```text
【环境/风格】户外岩石登山：腕表站在高山花岗岩岩脚上，岩面粗糙带地衣，远处蓝色山脊与山谷虚化；左侧傍晚金色阳光，清晰阴影，金属表壳反射暖光与天空蓝。橙色登山绳与钢扣只放在画面最右侧边缘，与腕表保持明显距离，不接触、不遮挡腕表；腕表底部与岩面之间有一条清晰的深色接触阴影。硬核户外工具表广告。
English: champagne-gold chronograph watch standing on a granite mountain ledge at golden hour; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, surface).

【产品外观】香槟金色金属表壳的多功能计时腕表，八角形表圈带银色螺丝和按键，黑色表盘、金色大号数字 12/3/6/9 与指针、下方液晶小窗，金色菱格纹表带与灰色塑料部件。严格保持图1中腕表的轮廓、比例、画面位置和视角完全不变，表盘指针位置与大号数字不变，不新增文字或 Logo。
【环境/风格】户外岩石登山：腕表站在高山花岗岩岩脚上，岩面粗糙带地衣，远处蓝色山脊与山谷虚化；左侧傍晚金色阳光，清晰阴影，金属表壳反射暖光与天空蓝。橙色登山绳与钢扣只放在画面最右侧边缘，与腕表保持明显距离，不接触、不遮挡腕表；腕表底部与岩面之间有一条清晰的深色接触阴影。硬核户外工具表广告。
English: champagne-gold chronograph watch standing on a granite mountain ledge at golden hour; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the watch must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, touching the rock at the same place). Only replace the grey studio background and floor with the environment, and relight the watch to match. Do not crop, zoom, rotate or move the watch. Nothing touches or overlaps the watch outline. Keep the dial layout; do not invent new text. No watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9: a rugged granite rock ledge high on a mountain at golden hour, camera low and close to the rock surface. Textured grey granite with lichen and small grit in the foreground, a coiled orange climbing rope and a carabiner lying off to the side, distant blue mountain ridges and a valley softly blurred in the background, warm late-afternoon sun from the left with crisp shadows, clear sky. Empty center area on the rock where a product could rest. Outdoor adventure tool-watch advertising mood. No people, no watches, no products, no text, no watermark.
```
</details>

**采用**：第 2 次（重试）

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 96.4% | >95% |
| 外轮廓 ≤3 px | 70%（≤6 px 78%） | ≥80% |
| 底部偏差 | +0 px | <5 px |
| 内部线条 ≤3 px | 85% | 参考 |
| bbox 偏差 L/R/T | +1 / +18 / -1 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 91% | 参考（不依赖分割） |
| 结论 | ❌ 未达标 | |

> 未达标原因：IoU 与底部偏差达标，外轮廓 ≤3 px 只有 70%。叠图显示表壳本身与 Blender 轮廓重合，但两次生成都把钢扣/登山绳放在表壳右侧紧贴处（bbox 右侧 +18 px），GrabCut 把它并进了腕表。表盘微小文字有轻微变形。

- 其他尝试 `attempts/rock_try1.png`：第 1 次：环境段含“一旁盘着橙色登山绳和钢扣”，钢扣贴着表壳右侧，底部多出岩石阴影。IoU 95.0%，外轮廓 ≤3 px 68%，底部 +14 px，补充边缘指标 93%，未达标。

