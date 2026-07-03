---
title: PhysSplat / Sim Anything
id: video2mesh-object-simulation-physsplat-sim-anything
category: 调研目录
visibility: public
summary: 这条线尝试给 3DGS 注入物理或动态信息，思想和分层代理不同：它更关注 dynamic Gaussian，而不是 visual mesh + collider 分工。
tags:
  - 物体仿真
  - Research Catalog
---

# PhysSplat / Sim Anything

## 简介

这条线尝试给 3DGS 注入物理或动态信息，思想和分层代理不同：它更关注 dynamic Gaussian，而不是 visual mesh + collider 分工。

## 输入与输出

输入：3DGS、语义、物理属性或交互条件。输出：带动态/物理含义的 Gaussian 表示。

## 在 Video2Mesh 中的位置

P2/P3 跟踪方向；模型未完全开源时不能作为主链路依赖。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
