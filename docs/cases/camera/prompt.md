# 案例五：复古相机 · 复古书房 / 街头胶片风

> 本案例的场景图由 Hark 的图像生成工具按插件的提示词结构与参考图分组生成（与单椅案例相同的方法），用于演示插件工作流；不是插件内 Codex / Antigravity Provider 的直接输出。

> **2026-10-07 重做（第 3、4 次）**：第 1 版产品外观写错了材质——写成“木质机身、黄铜镜头”，而模型实际是**黑色皮革包覆机身 + 银色镀铬金属镜头/前组支架**，只有三脚架是木质。本版按 base.png 重写了【产品外观】（银色金属镜头、黑色皮革机身、黑色云台、胡桃木双杆三脚架），重新生成了两张环境参考图（街头参考不再出现“Caf”字样）和两个场景；为了让测量更可靠，场景改成相机背后是浅色墙面、脚下是浅色地面/地毯。第 1、2 次结果保留在 `attempts/`。

## 模型与授权

- 模型：Khronos glTF Sample Assets · **AntiqueCamera** — https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/AntiqueCamera
- 授权：© 2018 UX3D，CC0 1.0（https://creativecommons.org/publicdomain/zero/1.0/）；作者 Maximilian Kamps。模型上的 UX3D 标志为 UX3D 商标
- 署名：Maximilian Kamps（UX3D）
- 处理：整机连三脚架一起作为产品。
- 环境参考图（refs/）全部由图像生成工具生成，无第三方版权素材。

## Blender 底图

| 底图（材质渲染，作为 Camera Base） | 白模 | Mask |
|---|---|---|
| ![](base.png) | ![](clay.png) | ![](mask.png) |

- Blender 4.3.2（Debian arm64 原生），Cycles CPU 64 spp、无降噪，AgX，960×540，浅灰地面 + 两盏面光（与单椅脚本相同的布光）。
- 机位参数（`tools/render_case.py`）：AZ=-40 EL=0.65 TZ=0.5 FILL=0.86（3/4 左前方，站立视高略俯视；50 mm）。
- Mask：透明背景渲染的 alpha>16 外轮廓填充。
- 底图里的真实材质：深灰黑皮革纹机身、黑色褶皱风箱、银白镀铬镜头与前组支架/导轨、黑色云台（银色小圆钉、左侧手柄）、银色连接盘、做旧胡桃木双杆三脚架、浅色金属包脚。

## 提示词（插件里这样填）

### 产品外观（固定，两个场景共用）

```text
【产品外观】复古折叠式风箱相机：机身为深灰黑色皮革包覆的箱体，黑色褶皱皮质风箱；镜头、镜头板、前组支架和镜头下方向右伸出的导轨平板为银色亮面金属（镀铬质感），镜头中心为深色玻璃；机身下方黑色金属云台（点缀银色小圆钉，左侧伸出黑色手柄），银色金属连接盘；安装在做旧的胡桃木三脚架上，每条腿是两根并排木条组成的宽扁双杆结构（侧面有浅色木纹），腿宽与图1完全一致、不要画细，脚末端为浅色金属包脚。严格保持图1中相机和三脚架的轮廓、比例、画面位置和视角完全不变，三条脚架的角度、宽度和落地点不变，镜头保持银色金属，不改成黄铜或金色，不添加文字或 Logo。
```

> 修正说明：第 1、2 次使用的旧版本是 `【产品外观】复古风箱式大画幅相机，木质机身配黑色皮革风琴腔体、黄铜镜头与金属件，安装在三脚木质三脚架上，脚架末端为金属脚尖。严格保持图1中相机和三脚架的轮廓、比例、画面位置和视角完全不变，三条脚架的角度和落地点不变，不添加文字或 Logo。` ——“木质机身”“黄铜镜头”与模型不符（黄铜→银色）。第 3 次用了较短的银色版本，第 4 次（采用）补充了脚架“宽扁双杆”、云台手柄、导轨平板的描述，因为第 3 次生成图的脚架被画细、手柄丢失。

## 插件设置

| 项 | 设置 |
|---|---|
| 参考图分组 | 产品造型：不放（颜色/材质以 Blender 材质为准）；人物：不放；环境／风格：每个场景 1 张，作为**主参考**（第一张） |
| 渲染模式 | 标准（Structure Packet：Mask / Depth / Normal / Silhouette） |
| 严格构图锁定 | 开 |
| 结构控制图 | 开 |
| 局部结构修复 | 开 |
| 身份资产空间保护（Identity Preserve） | 开启（机身有 UX3D 标志），扩边 2 px；硬恢复关闭 |
| 生成张数 | 1 |
| 输出 | 16:9，实际 1376×768 |

## 场景：复古书房（scene_study.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_study.png) | ![](scene_study.png) | ![](checks/scene_study_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：浅鼠尾草绿护墙板、大块米白地毯、左侧窗光 + 右侧黄铜台灯暖光、胶片颗粒；不取：书架与书桌的具体位置。

**环境/风格（每个场景单独填）**

```text
【环境/风格】复古书房：相机三条脚都稳稳站在一块大块浅米白色羊毛地毯的中央（地毯边缘离脚尖很远），地毯外露出浅橡木人字拼地板；相机正后方是从地脚到顶的浅鼠尾草绿色护墙板，深色机身和胡桃木脚架在浅绿背景前轮廓清晰；书架和旧皮面书（书脊无文字）只在画面左右两侧，右侧红木书桌上黄铜台灯发出暖黄钨丝光，左侧窗户投入柔和金色窗光；暖调复古、明亮通透，轻微胶片颗粒，银色镜头上有暖色反光，脚尖在地毯上有轻柔接触阴影。
English: antique black folding bellows camera with a silver chrome lens on a walnut wooden tripod, standing in the middle of a large cream rug in a bright 1920s study with pale sage-green panelled walls; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, wall, floor).

【产品外观】复古折叠式风箱相机：机身为深灰黑色皮革包覆的箱体，黑色褶皱皮质风箱；镜头、镜头板、前组支架和镜头下方向右伸出的导轨平板为银色亮面金属（镀铬质感），镜头中心为深色玻璃；机身下方黑色金属云台（点缀银色小圆钉，左侧伸出黑色手柄），银色金属连接盘；安装在做旧的胡桃木三脚架上，每条腿是两根并排木条组成的宽扁双杆结构（侧面有浅色木纹），腿宽与图1完全一致、不要画细，脚末端为浅色金属包脚。严格保持图1中相机和三脚架的轮廓、比例、画面位置和视角完全不变，三条脚架的角度、宽度和落地点不变，镜头保持银色金属，不改成黄铜或金色，不添加文字或 Logo。
【环境/风格】复古书房：相机三条脚都稳稳站在一块大块浅米白色羊毛地毯的中央（地毯边缘离脚尖很远），地毯外露出浅橡木人字拼地板；相机正后方是从地脚到顶的浅鼠尾草绿色护墙板，深色机身和胡桃木脚架在浅绿背景前轮廓清晰；书架和旧皮面书（书脊无文字）只在画面左右两侧，右侧红木书桌上黄铜台灯发出暖黄钨丝光，左侧窗户投入柔和金色窗光；暖调复古、明亮通透，轻微胶片颗粒，银色镜头上有暖色反光，脚尖在地毯上有轻柔接触阴影。
English: antique black folding bellows camera with a silver chrome lens on a walnut wooden tripod, standing in the middle of a large cream rug in a bright 1920s study with pale sage-green panelled walls; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the camera and tripod must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, same leg widths, tripod feet touching the floor at the same three points). Only replace the grey studio background and floor with the environment, and relight the camera to match. Do not crop, zoom, rotate or move anything; keep the background behind the thin tripod legs clearly distinct from the legs. No readable text, no logos, no watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9: an empty sunlit vintage 1920s study room interior, viewed at standing eye level slightly looking down. Center of the frame: a wall fully covered in muted pale sage-green painted wood panelling (from floor to ceiling, including the lower wainscot, all the same pale sage green), and a large plain light cream wool rug covering most of the visible floor, extending well toward the viewer, over a pale oak herringbone floor visible only at the edges. The center of the room is completely empty. Tall dark wood bookshelves with old leather-bound books (blank spines, no lettering) only at the far left and far right edges, a brass desk lamp glowing warm tungsten on a mahogany desk at the right edge, soft golden window light from the left. Warm, bright, airy vintage mood, gentle film grain. Absolutely no camera, no tripod, no easel, no stand, nothing in the center, no people, no text, no letters, no watermark.
```
</details>

**采用**：第 4 次（本轮第 2 次）

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 93.7% | >95% |
| 外轮廓 ≤3 px | 91%（≤6 px 94%） | ≥80% |
| 底部偏差 | +3 px | <5 px |
| 内部线条 ≤3 px | 88% | 参考 |
| bbox 偏差 L/R/T | +1 / +6 / +0 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 97% | 参考（不依赖分割） |
| 结论 | ❌ 未达标（IoU 差 1.3 个点；外轮廓与底部达标） | |

> 未达标原因：IoU 93.7%。差异集中在细部：云台左侧手柄、镜头下方向右伸出的导轨平板、右前脚架外侧的浅色木条边，GrabCut 没有分到产品里（也有几处是生成图把这些细件画得比 Blender 略窄）。机身、风箱、三条脚架和落地点与 Blender 轮廓基本重合。
> 外观：镜头前组、支架和导轨为银色金属，但在暖色台灯光下镜头外圈带明显暖金色反光，近看偏“旧铜/香槟色”，没有完全达到 base.png 那种冷白镀铬；如需更准确，下次可把书房光线改为中性日光、去掉“银色镜头上有暖色反光”。无可读文字。

### 本场景其他尝试

- `attempts/study_try1.png`（第 1 次，旧采用版）：旧产品外观（黄铜镜头）+ 旧参考 `attempts/ref_study_try1-2.png`（深色书房）。IoU 74.3%，外轮廓 ≤3 px 40%，底部 -8 px，补充边缘 98%。镜头被画成黄铜色。
- `attempts/study_try2.png`（第 2 次）：同上并附 Blender Mask；镜头变银白但机身发虚。IoU 73.0%，外轮廓 ≤3 px 39%，底部 -13 px，补充边缘 97%。
- `attempts/study_try3.png`（第 3 次，本轮第 1 次）：银色版产品外观（较短版本）+ 参考 `attempts/ref_study_try3.png`（奶油色墙 + 浅橡木护墙板 + 米白地毯）。IoU 87.2%，外轮廓 ≤3 px 80%，底部 +3 px，bbox 右 +20 px，补充边缘 97%，未达标：地毯边缘正好在脚尖高度，被并入产品；脚架被画细。产品外观与环境提示词：

```text
【产品外观】复古折叠式风箱相机：机身为黑色皮革包覆的深色箱体，黑色褶皱皮质风箱；镜头、镜头板和前组支架为银色亮面金属（镀铬质感），镜头中心为深色玻璃；机身下方黑色金属云台点缀银色小圆钉，银色金属连接盘；安装在做旧的胡桃木三脚架上，脚架末端为银色金属包脚。严格保持图1中相机和三脚架的轮廓、比例、画面位置和视角完全不变，三条脚架的角度和落地点不变，镜头保持银色金属，不改成黄铜或金色，不添加文字或 Logo。
【环境/风格】复古书房：相机支在一块浅米白色羊毛地毯上，地毯下是浅蜂蜜色橡木人字拼地板；相机正后方是暖奶油色墙面和浅橡木护墙板，深色机身和胡桃木脚架在浅色背景前轮廓清晰；书架和旧皮面书（书脊无文字）只在画面左右两侧，右侧红木书桌上黄铜台灯发出暖黄钨丝光，左侧窗户投入柔和金色窗光；琥珀蜂蜜色调，明亮通透，轻微胶片颗粒，银色镜头上有暖色反光，脚尖在地毯上有轻柔接触阴影。
```

## 场景：街头胶片风（scene_street.png）

| 环境参考（主参考） | 生成结果 | 轮廓检测叠图（红=Blender，绿=GrabCut） |
|---|---|---|
| ![](refs/ref_street.png) | ![](scene_street.png) | ![](checks/scene_street_overlay.jpg) |

**环境／风格参考 · “参考什么”**：取：Portra 400 胶片色调与颗粒、粉彩薄荷绿灰泥墙、浅灰弹石路、左侧柔和暖光；不取：木门和自行车的位置。参考图已重新生成，**没有任何招牌或可读文字**（旧参考的“Caf”问题已去除）。

**环境/风格（每个场景单独填）**

```text
【环境/风格】街头胶片风：相机支在欧洲老城小巷浅灰白色的石灰岩弹石路上；相机正后方是虚化的粉彩淡薄荷绿色灰泥墙，深色机身和胡桃木脚架在浅绿背景前轮廓清晰；两侧虚化的绿色百叶窗、木门、米白色遮阳棚（无任何文字）和靠墙的自行车；左侧傍晚柔和暖光，阴影短而淡，脚尖在弹石上有轻柔接触阴影；Kodak Portra 400 胶片色调，细腻颗粒，高光微褪色。
English: antique black folding bellows camera with a silver chrome lens on a walnut wooden tripod on pale limestone cobblestones in an old European lane, pastel mint-green stucco wall behind, Portra 400 film look; keep the exact silhouette, scale, position and camera angle of image 1.
```

<details><summary>本次实际发送给生图模型的完整指令（含插件严格构图锁定会追加的规则）</summary>

```text
Image 1 is the Blender Camera Base (composition authority). Image 2 is the environment main reference (lighting, mood, ground, film look).

【产品外观】复古折叠式风箱相机：机身为深灰黑色皮革包覆的箱体，黑色褶皱皮质风箱；镜头、镜头板、前组支架和镜头下方向右伸出的导轨平板为银色亮面金属（镀铬质感），镜头中心为深色玻璃；机身下方黑色金属云台（点缀银色小圆钉，左侧伸出黑色手柄），银色金属连接盘；安装在做旧的胡桃木三脚架上，每条腿是两根并排木条组成的宽扁双杆结构（侧面有浅色木纹），腿宽与图1完全一致、不要画细，脚末端为浅色金属包脚。严格保持图1中相机和三脚架的轮廓、比例、画面位置和视角完全不变，三条脚架的角度、宽度和落地点不变，镜头保持银色金属，不改成黄铜或金色，不添加文字或 Logo。
【环境/风格】街头胶片风：相机支在欧洲老城小巷浅灰白色的石灰岩弹石路上；相机正后方是虚化的粉彩淡薄荷绿色灰泥墙，深色机身和胡桃木脚架在浅绿背景前轮廓清晰；两侧虚化的绿色百叶窗、木门、米白色遮阳棚（无任何文字）和靠墙的自行车；左侧傍晚柔和暖光，阴影短而淡，脚尖在弹石上有轻柔接触阴影；Kodak Portra 400 胶片色调，细腻颗粒，高光微褪色。
English: antique black folding bellows camera with a silver chrome lens on a walnut wooden tripod on pale limestone cobblestones in an old European lane, pastel mint-green stucco wall behind, Portra 400 film look; keep the exact silhouette, scale, position and camera angle of image 1.

Hard rules: output 16:9, same framing as image 1; the camera and tripod must occupy exactly the same pixels as in image 1 (same outline, same size, same position, same perspective, same leg widths, tripod feet touching the ground at the same three points). Only replace the grey studio background and floor with the environment, and relight the camera to match. Do not crop, zoom, rotate or move anything; keep the background behind the thin tripod legs clearly distinct from the legs. No readable text, letters or signs anywhere, no logos, no watermark, no people.
```
</details>

<details><summary>参考图生成提示词</summary>

```text
Photographic environment reference plate, 16:9, analog film look (Kodak Portra 400, soft grain, slightly faded highlights): an old European town lane in soft late-afternoon light, viewed at standing eye level slightly looking down at pale light grey limestone cobblestone pavement. Directly behind the empty center area: a softly blurred pastel pale mint / sage-green stucco facade with a wooden door far to one side. At the sides, softly blurred: a green shuttered window, a plain cream awning with absolutely no lettering, a bicycle leaning on a wall at the far left. Soft diffused warm light from the left, gentle short shadows. The empty center area is clear. No people, no cameras, no tripods, no shop signs, no text, no letters, no numbers, no logos, no house numbers, no watermark.
```
</details>

**采用**：第 4 次（本轮第 2 次）

| 指标 | 结果 | 门槛 |
|---|---|---|
| 轮廓 IoU | 90.4% | >95% |
| 外轮廓 ≤3 px | 84%（≤6 px 87%） | ≥80% |
| 底部偏差 | +2 px | <5 px |
| 内部线条 ≤3 px | 84% | 参考 |
| bbox 偏差 L/R/T | +1 / -1 / +0 px | 参考 |
| 补充：Blender 轮廓 3 px 内有生成图边缘 | 100% | 参考（不依赖分割） |
| 结论 | ❌ 未达标（IoU；外轮廓与底部达标） | |

> 未达标原因：IoU 90.4%。右前脚架外侧那条浅色木条被画得更窄/和浅绿墙面融在一起，云台左侧手柄落在绿色百叶窗前被漏分，导轨平板右端也漏掉；bbox 四边偏差都在 1 px 内，补充边缘指标 100%，位置没有跑。外观：镜头、支架、导轨为银色镀铬，与模型一致；无可读文字（旁边的小门牌是空白的）。

### 本场景其他尝试

- `attempts/street_try1.png`（第 1 次，旧采用版）：旧产品外观（黄铜镜头）+ 旧参考 `attempts/ref_street_try1-2.png`（参考图右上有“Caf”字样）。IoU 89.4%，外轮廓 ≤3 px 86%，底部 +0 px，补充边缘 99%。镜头被画成黄铜色。
- `attempts/street_try2.png`（第 2 次）：附 Blender Mask；遮阳棚出现 “Café” 文字。IoU 90.4%，外轮廓 ≤3 px 87%，底部 +3 px，补充边缘 100%。
- `attempts/street_try3.png`（第 3 次，本轮第 1 次）：银色版产品外观（较短版本）+ 参考 `attempts/ref_street_try3.png`（浅奶油色灰泥墙，无文字）。IoU 87.4%，外轮廓 ≤3 px 81%，底部 +2 px，补充边缘 99%，未达标：右前脚架被画细，其受光的浅色侧面与奶油色墙面接近被漏分。镜头为银色，无文字。产品外观与环境提示词：

```text
【产品外观】复古折叠式风箱相机：机身为黑色皮革包覆的深色箱体，黑色褶皱皮质风箱；镜头、镜头板和前组支架为银色亮面金属（镀铬质感），镜头中心为深色玻璃；机身下方黑色金属云台点缀银色小圆钉，银色金属连接盘；安装在做旧的胡桃木三脚架上，脚架末端为银色金属包脚。严格保持图1中相机和三脚架的轮廓、比例、画面位置和视角完全不变，三条脚架的角度和落地点不变，镜头保持银色金属，不改成黄铜或金色，不添加文字或 Logo。
【环境/风格】街头胶片风：相机支在欧洲老城小巷浅灰白色的石灰岩弹石路上；相机正后方是虚化的浅奶油色/淡杏色灰泥墙，深色机身和胡桃木脚架在浅色背景前轮廓清晰；两侧虚化的绿色百叶窗、条纹遮阳棚（无任何文字）和靠墙的自行车；傍晚柔和暖光，阴影短而淡，脚尖在弹石上有轻柔接触阴影；Kodak Portra 400 胶片色调，细腻颗粒，高光微褪色。
```
