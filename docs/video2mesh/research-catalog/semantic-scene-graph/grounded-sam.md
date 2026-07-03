---
title: Grounded-SAM / Open-vocabulary Detection
id: video2mesh-semantic-scene-graph-grounded-sam
category: 调研目录
visibility: public
summary: Grounded-SAM 类路线把文本检测和 SAM 分割结合，能给 object mask 加上开放词汇标签。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Grounded-SAM / Open-vocabulary Detection

![Grounded-SAM](../assets/stage-semantics.svg "Grounded-SAM 类路线把文本检测框和 SAM mask 结合，得到带开放词汇标签的对象区域")

## 链接

- Grounding DINO GitHub: https://github.com/IDEA-Research/GroundingDINO
- Grounded-Segment-Anything GitHub: https://github.com/IDEA-Research/Grounded-Segment-Anything
- Grounding DINO paper: https://arxiv.org/abs/2303.05499
- Segment Anything: https://segment-anything.com/

## 摘要要点

GroundingDINO 做开放词汇目标检测：给定文本类别或自然语言短语，输出图像中的候选框；SAM 再把框转成精细 mask。Grounded-SAM 的实用价值在于把“开放词汇类别”和“高质量分割边界”连接起来。

对 Video2Mesh 来说，它能从 bedroom scan 中发现 bed、window、curtain、floor、nightstand、lamp 等对象，为每个 object id 生成多帧 masks。后续再通过投影/投票把这些 2D masks 绑定到 3D 点、Gaussian 或 mesh face。

## Pipeline

| 阶段 | 作用 |
|---|---|
| text prompt / class list | 设定需要发现的物体类别 |
| GroundingDINO detection | 输出开放词汇 boxes 和 scores |
| SAM mask prediction | 用 boxes 提示 SAM 生成 masks |
| tracking / multi-view fusion | 合并跨帧 object id |
| 3D semantic transfer | 回灌到 point cloud / mesh face sidecar |

## 输入与输出

输入：图像、文本 prompt 或类别列表。输出：带 label/score 的 2D masks、object candidate 列表和后续 3D 语义融合证据。

## 在 Video2Mesh 中的位置

P1 提升 object label 和 affordance。正式 semantic mesh 结果中已经出现 GroundingDINO object discovery、SAM/SAM2 tracking 和 3D object masks 的产物，它是下一步 object split 和交互属性的入口。

## 接入判断

- P0：不阻塞几何闭环，但可作为可选 semantic path。
- P1：进入 object split、物体补全和交互属性路线。
- 风险：类别 prompt 需要针对室内场景维护，过宽会误检，过窄会漏物体。
