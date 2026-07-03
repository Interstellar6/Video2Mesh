---
title: NeuS / VolSDF
id: video2mesh-mesh-reconstruction-neus-volsdf
category: 调研目录
visibility: public
summary: Neural SDF 路线能做高质量隐式表面重建，但训练和集成成本高。
tags:
  - Mesh 重建
  - Research Catalog
---

# NeuS / VolSDF

## 简介

Neural SDF 路线能做高质量隐式表面重建，但训练和集成成本高。

## 输入与输出

输入：多视角图像和相机。输出：SDF / mesh。

## 在 Video2Mesh 中的位置

离线高质量资产候选，不适合当前主链路快速闭环。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
