---
title: Scene Graph / VLM
id: video2mesh-semantic-scene-graph-scene-graph-vlm
category: 调研目录
visibility: public
summary: VLM 和 scene graph 用来描述物体关系、空间布局和可交互属性。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Scene Graph / VLM

![Scene Graph / VLM](../assets/stage-semantics.svg "Scene graph 和 VLM 将几何物体扩展成可查询的关系、支撑和交互属性")

## 链接

- ConceptGraphs project: https://concept-graphs.github.io/
- OpenScene project: https://pengsongyou.github.io/openscene
- LLaVA project: https://llava-vl.github.io/
- GPT-4o / VLM APIs can provide object description and QA when local model is not fixed.

## 简介

Scene graph / VLM 的任务是把“物体在哪里”扩展成“物体之间是什么关系、能不能移动、是不是支撑面、材质大概是什么、交互应该如何处理”。这对 simulator asset bundle 很重要，因为物理参数和交互规则不能只从三角网格自动得到。

VLM 可以从 object crop、多视角截图和语义 mesh 中估计类别、材质、可抓取性、支撑关系和简短描述；scene graph 则把这些信息结构化为 nodes/edges，供 viewer 和引擎适配使用。

## Pipeline

| 阶段 | 作用 |
|---|---|
| object candidates | 来自 semantic sidecar 或 object split |
| visual evidence | 多视角 crops、mesh screenshot、splat screenshot |
| VLM inference | 估计 label、material、movable、support、affordance |
| relation graph | 建立 on/inside/near/support/occluding 等关系 |
| asset sidecar | 写入 simulator_asset_bundle metadata |

## 输入与输出

输入：图像、语义 mesh、object crops、bbox、support planes。输出：object relation、affordance、材质和物理属性 hints、可读描述。

## 在 Video2Mesh 中的位置

P1/P2，让场景从“能看见”变成“能查询”。它可以为 bed/nightstand/lamp/curtain 等 object split 生成初始 metadata，再由人工或规则 QA。

## 接入判断

- P0：不阻塞几何闭环。
- P1：用于 simulator asset bundle 的 material/body_type/affordance 初稿。
- 风险：VLM 输出必须带 provenance 和 confidence，不能直接当真值物理参数。
