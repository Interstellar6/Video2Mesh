---
title: Mesh Face Sidecar
id: video2mesh-semantic-scene-graph-mesh-face-sidecar
category: 调研目录
visibility: public
summary: mesh face sidecar 把 face index 映射到 object id、label、material 和交互属性，不把语义烘死在颜色里。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Mesh Face Sidecar

## 简介

mesh face sidecar 把 face index 映射到 object id、label、material 和交互属性，不把语义烘死在颜色里。

## 输入与输出

输入：mesh、semantic points/masks、投票结果。输出：face_labels.json 或等价 sidecar。

## 在 Video2Mesh 中的位置

P0 交互查询关键合同。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
