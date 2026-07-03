---
title: Semantic Splats
id: video2mesh-semantic-scene-graph-semantic-splats
category: 调研目录
visibility: public
summary: semantic splats 把 Gaussian 或点云和语义概率绑定，适合在 visual layer 上查询和渲染标签。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Semantic Splats

## 简介

semantic splats 把 Gaussian 或点云和语义概率绑定，适合在 visual layer 上查询和渲染标签。

## 输入与输出

输入：3DGS/点云 + 2D masks。输出：semantic/probability PLY。

## 在 Video2Mesh 中的位置

P0/P1 语义可视化，不替代 mesh face sidecar。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
