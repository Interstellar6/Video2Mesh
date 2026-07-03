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

## 简介

VLM 和 scene graph 用来描述物体关系、空间布局和可交互属性。

## 输入与输出

输入：图像、语义 mesh、object crops。输出：object relation、affordance、描述。

## 在 Video2Mesh 中的位置

P1/P2，让场景从“能看见”变成“能查询”。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
