---
title: TRELLIS
id: video2mesh-object-mesh-completion-trellis
category: 调研目录
visibility: public
summary: TRELLIS 代表新一代 3D asset generation 模型，适合生成更完整的物体资产。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# TRELLIS

## 简介

TRELLIS 代表新一代 3D asset generation 模型，适合生成更完整的物体资产。

## 输入与输出

输入：单图或多模态条件。输出：3D asset。

## 在 Video2Mesh 中的位置

P1/P2 物体补全候选，重点测试遮挡物体。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
