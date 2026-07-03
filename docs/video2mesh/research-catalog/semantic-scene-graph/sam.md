---
title: Segment Anything / SAM
id: video2mesh-semantic-scene-graph-sam
category: 调研目录
visibility: public
summary: SAM 提供 2D mask 生成和交互式分割，是 Video2Mesh 2D-to-3D 语义融合的基础之一。
tags:
  - 语义与 Scene Graph
  - Research Catalog
---

# Segment Anything / SAM

## 简介

SAM 提供 2D mask 生成和交互式分割，是 Video2Mesh 2D-to-3D 语义融合的基础之一。

## 输入与输出

输入：图像和点/框/自动提示。输出：2D masks。

## 在 Video2Mesh 中的位置

P0 语义输入，但要配合跟踪、投影和可见性过滤。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
