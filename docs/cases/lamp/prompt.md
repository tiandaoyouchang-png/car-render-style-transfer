# 案例六：幻彩玻璃台灯 · 极简卧室夜晚 / 咖啡馆

> 本案例的场景图由 Hark 的图像生成工具按插件的提示词结构与参考图分组生成（与单椅案例相同的方法），用于演示插件工作流；不是插件内 Codex / Antigravity Provider 的直接输出。

## 模型与授权

- 模型：Khronos glTF Sample Assets · **IridescenceLamp** — https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/IridescenceLamp
- 授权：© 2022 Wayfair LLC，CC BY 4.0（https://creativecommons.org/licenses/by/4.0/）；模型与贴图 Eric Chadwick
- 署名：Eric Chadwick（Wayfair）
- 处理：原样导入。
- 环境参考图（refs/）全部由图像生成工具生成，无第三方版权素材。

## Blender 底图

| 底图（材质渲染，作为 Camera Base） | 白模 | Mask |
|---|---|---|
| ![](base.png) | ![](clay.png) | ![](mask.png) |

- Blender 4.3.2（Debian arm64 原生），Cycles CPU 64 spp、无降噪，AgX，960×540，浅灰地面 + 两盏面光（与单椅脚本相同的布光）。
- 机位参数（`tools/render_case.py`）：AZ=-30 EL=0.55 FILL=0.8（3/4 左前方，坐姿视高略俯视；50 mm）。
- Mask：透明背景渲染的 alpha>16 外轮廓填充。

## 提示词（插件里这样填）

### 产品外观（固定，两个场景共用）

```text
【产品外观】台灯：灰褐色（taupe）亚麻圆柱形灯罩，灯座为带幻彩（彩虹薄膜）光泽的透明球形玻璃，球内可见细金属管，亮银色金属灯颈与圆形底座。材质与颜色以图1的 Blender 材质为准。严格保持图1中台灯的轮廓、比例、画面位置和视角完全不变，灯罩形状与球形灯座不变，不添加文字或 Logo。
```

## 插件设置

| 项 | 设置 |
|---|---|
| 参考图分组 | 产品造型：不放（颜色/材质以 Blender 材质为准）；人物：不放；环境／风格：每个场景 1 张，作为**主参考**（第一张） |
| 渲染模式 | 标准（Structure Packet：Mask / Depth / Normal / Silhouette） |
| 严格构图锁定 | 开 |
| 结构控制图 | 开 |
| 局部结构修复 | 开 |
| 身份资产空间保护（Identity Preserve） | 关闭（无 Logo） |
| 生成张数 | 1 |
| 输出 | 16:9，实际 1376×768 |

## 场景：极简卧室夜晚（scene_bedroom.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_bedroom.png) | ![](scene_bedroom.png) | ![](checks/scene_bedroom_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：深夜室内、窗外深蓝夜色与微弱冷月光、台灯暖光晕、日式极简材质；不取：参考图里的物件位置。

**环境/风格（每个场景单独填）**

```text
【环境/风格】极简卧室夜晚：深夜，房间偏暗，台灯是主光源已点亮，灰褐色灯罩透出 2700K 暖黄光，在暖灰色微水泥墙和浅橡木床头柜面上形成柔和光晕；背景是米白亚麻床品的低矮床，薄纱窗帘外深蓝夜空，窗边微弱冷色月光；球形玻璃灯座折射暖光并带幻彩高光，玻璃球轮廓有清晰的亮边。安静、温馨的日式极简家居广告。
English: table lamp with taupe linen drum shade and iridescent glass globe base, switched on as the main light, on an oak nightstand in a dark minimalist Japandi bedroom late at night; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, surface).

【产品外观】台灯：灰褐色（taupe）亚麻圆柱形灯罩，灯座为带幻彩（彩虹薄膜）光泽的透明球形玻璃，球内可见细金属管，亮银色金属灯颈与圆形底座。材质与颜色以图1的 Blender 材质为准。严格保持图1中台灯的轮廓、比例、画面位置和视角完全不变，灯罩形状与球形灯座不变，不添加文字或 Logo。
【环境/风格】极简卧室夜晚：深夜，房间偏暗，台灯是主光源已点亮，灰褐色灯罩透出 2700K 暖黄光，在暖灰色微水泥墙和浅橡木床头柜面上形成柔和光晕；背景是米白亚麻床品的低矮床，薄纱窗帘外深蓝夜空，窗边微弱冷色月光；球形玻璃灯座折射暖光并带幻彩高光，玻璃球轮廓有清晰的亮边。安静、温馨的日式极简家居广告。
English: table lamp with taupe linen drum shade and iridescent glass globe base, switched on as the main light, on an oak nightstand in a dark minimalist Japandi bedroom late at night; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the lamp must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, base touching the surface at the same place). Only replace the grey studio background and floor with the environment, and relight the lamp to match. Do not crop, zoom, rotate or move the lamp. No text, no logos, no watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9: a minimalist Japandi bedroom at night, camera at seated eye level looking slightly down at the top of a light oak nightstand in the foreground. Behind: a low bed with off-white linen bedding, a plain warm-grey plaster wall, a tall window with sheer curtains showing deep blue night sky. Lighting: very dim cool moonlight from the window, and a warm 2700K glow pool on the nightstand and wall as if from a bedside lamp (lamp itself not shown). Calm, quiet, cozy mood. Empty center of the nightstand top where a table lamp would stand. No lamps, no products, no people, no text, no watermark.
```
</details>

**采用**：第 3 次（产品外观改为 taupe 灯罩后的第 2 次）

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 66.8% | >95% |
| 外轮廓 ≤3 px | 47%（≤6 px 58%） | ≥80% |
| 底部偏差 | -199 px | <5 px |
| 内部线条 ≤3 px | 75% | 参考 |
| bbox 偏差 L/R/T | +1 / -1 / +2 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 100% | 参考（不依赖分割） |
| 结论 | ❌ 未达标 | |

> 未达标原因：测量失败而不是错位。透明玻璃球灯座让 GrabCut 只保留了灯罩（底部 -199 px）；叠图上整盏灯与 Blender 轮廓逐像素重合，补充边缘指标 100%。第 1 次（白色灯罩提示词）按统一方法达标（IoU 96.4%），但灯罩颜色不忠实，所以没采用。

- 其他尝试 `attempts/bedroom_try1_white-shade-prompt.png`：第 1 次：产品外观写成“白色圆柱形布艺灯罩”（与模型 taupe 灯罩不符），灯罩被画成米白；指标达标（见下）但外观不忠实，弃用。IoU 96.4%，外轮廓 ≤3 px 86%，底部 -2 px，补充边缘指标 97%，达标。
- 其他尝试 `attempts/bedroom_try2.png`：第 2 次：改为 taupe 灯罩后的首版，画面接近黄昏、台灯不够亮。IoU 66.9%，外轮廓 ≤3 px 46%，底部 -199 px，补充边缘指标 97%，未达标。

## 场景：咖啡馆（scene_cafe.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_cafe.png) | ![](scene_cafe.png) | ![](checks/scene_cafe_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：左侧傍晚窗光斜射、琥珀蜂蜜色调、浅景深、胡桃木桌面；不取：拿铁和绿植的具体位置（要求不遮挡台灯）。

**环境/风格（每个场景单独填）**

```text
【环境/风格】咖啡馆：台灯放在胡桃木咖啡桌上，桌面一侧有拉花拿铁和小盆绿植（不遮挡台灯）；背景虚化的红砖墙、木架上的陶瓷杯、大窗和吊绿植，左侧傍晚阳光斜射进来，琥珀蜂蜜色调，浅景深；球形玻璃灯座折射窗光并带幻彩高光，底座在桌面有自然接触阴影。温暖的生活方式广告。
English: table lamp with taupe linen drum shade and iridescent glass globe base on a walnut café table, warm afternoon window light, latte and plant nearby; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, surface).

【产品外观】台灯：灰褐色（taupe）亚麻圆柱形灯罩，灯座为带幻彩（彩虹薄膜）光泽的透明球形玻璃，球内可见细金属管，亮银色金属灯颈与圆形底座。材质与颜色以图1的 Blender 材质为准。严格保持图1中台灯的轮廓、比例、画面位置和视角完全不变，灯罩形状与球形灯座不变，不添加文字或 Logo。
【环境/风格】咖啡馆：台灯放在胡桃木咖啡桌上，桌面一侧有拉花拿铁和小盆绿植（不遮挡台灯）；背景虚化的红砖墙、木架上的陶瓷杯、大窗和吊绿植，左侧傍晚阳光斜射进来，琥珀蜂蜜色调，浅景深；球形玻璃灯座折射窗光并带幻彩高光，底座在桌面有自然接触阴影。温暖的生活方式广告。
English: table lamp with taupe linen drum shade and iridescent glass globe base on a walnut café table, warm afternoon window light, latte and plant nearby; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the lamp must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, base touching the surface at the same place). Only replace the grey studio background and floor with the environment, and relight the lamp to match. Do not crop, zoom, rotate or move the lamp. Nothing overlaps the lamp outline. No readable text or menus, no logos, no watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9: a cozy specialty coffee shop in the late afternoon, camera at seated eye level looking slightly down at a walnut wood café table top in the foreground. On the table to the side: a ceramic latte cup with latte art and a small potted plant. Background softly blurred: exposed brick wall, wooden shelves with ceramic cups, large window with warm sunlight streaming in from the left, a few hanging plants. Warm honey tones, soft natural light, shallow depth of field. Empty center of the table top where a table lamp would stand. No lamps, no people, no readable text or menus, no watermark.
```
</details>

**采用**：第 2 次（产品外观改为 taupe 灯罩后的首版）

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 97.5% | >95% |
| 外轮廓 ≤3 px | 93%（≤6 px 99%） | ≥80% |
| 底部偏差 | -1 px | <5 px |
| 内部线条 ≤3 px | 77% | 参考 |
| bbox 偏差 L/R/T | +0 / -1 / -1 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 94% | 参考（不依赖分割） |
| 结论 | ✅ 达标 | |

- 其他尝试 `attempts/cafe_try1_white-shade-prompt.png`：第 1 次：产品外观写成“白色灯罩”，灯罩被画成白色；指标达标但外观不忠实，弃用。IoU 96.8%，外轮廓 ≤3 px 91%，底部 -1 px，补充边缘指标 99%，达标。

