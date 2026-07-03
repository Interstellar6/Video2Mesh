---
title: Surface-aware Gaussian 路线
id: video2mesh-visual-3dgs-surface-aware-gs
category: 调研目录
visibility: public
summary: SuGaR、2DGS、GOF 等都可以理解为把 Gaussian 表达往表面约束方向推进，以减少后续 mesh extraction 的不确定性。
tags:
  - 视觉重建与 3DGS
  - Research Catalog
---

# Surface-aware Gaussian 路线

## 简介

SuGaR、2DGS、GOF 等都可以理解为把 Gaussian 表达往表面约束方向推进，以减少后续 mesh extraction 的不确定性。

## 输入与输出

输入：训练图像或已有 3DGS。输出：更贴近表面的 Gaussian / mesh。

## 在 Video2Mesh 中的位置

P2 研究升级线，短期不替代 GraphDECO P0。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
