# 3.0.3 · Appearance-Only Prompt

## Prompt 职责重构

- 用户可见 Prompt 不再承担构图控制。
- AI 润色输出必须删除旧版本遗留的相机、构图、位置、尺度、bbox、轮心、裁切、透视、遮挡等 Structure 描述。
- Prompt 只描述 Appearance：产品/人物身份、材质、灯光、色调、风格、环境质感、摄影成像质感、后期和画质。
- Blender Camera Base + Structure Packet 独立承担 Camera / Composition / Geometry / Position / Scale / Rotation / Occlusion / Spatial Relationship。

## 参考图工作流

- 参考图区域位于 AI 润色 / 重新生成提示词按钮上方。
- 每张产品 / 人物 / 风格参考图右侧均有“参考什么”输入框。
- 用户填写后，只提取指定内容；如果填写内容涉及构图/机位/位置，Structure 部分会被忽略。
- 未填写时使用该类别默认职责。

## 最终渲染

- 最终 Provider 指令只保留必要的 Reference 角色说明，用于告诉模型 Mask / Depth / Normal / Silhouette / Part ID 各自是什么。
- 不再用文字重复 bbox、轮心、相机角度、zoom/pan/crop 等构图约束。
- Structure Packet 控制结构，Prompt 只控制 Appearance。
