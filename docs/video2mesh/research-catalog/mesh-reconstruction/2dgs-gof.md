---
title: 2DGS / GOF
id: video2mesh-mesh-reconstruction-2dgs-gof
category: 调研目录
visibility: public
summary: 2DGS 和 GOF 都从 Gaussian 表面/不透明场约束角度提升几何一致性，适合减少传统 3DGS mesh extraction 的问题。
tags:
  - Mesh 重建
  - Research Catalog
---

# 2DGS / GOF

## 简介

2DGS 和 GOF 都从 Gaussian 表面/不透明场约束角度提升几何一致性，适合减少传统 3DGS mesh extraction 的问题。

## 输入与输出

输入：训练图像或 Gaussian。输出：更适合 surface reconstruction 的表示和 mesh。

## 在 Video2Mesh 中的位置

P2/P3 研究升级，不直接进入 P0 collider。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
