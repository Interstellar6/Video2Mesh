---
title: GS2Mesh
id: video2mesh-mesh-reconstruction-gs2mesh
category: 调研目录
visibility: public
summary: GS2Mesh 的关键思想是利用训练好的 3DGS 渲染多视角/双目信息，再估计深度并做 TSDF fusion，比直接连 Gaussian center 更合理。
tags:
  - Mesh 重建
  - Research Catalog
---

# GS2Mesh

## 简介

GS2Mesh 的关键思想是利用训练好的 3DGS 渲染多视角/双目信息，再估计深度并做 TSDF fusion，比直接连 Gaussian center 更合理。

## 输入与输出

输入：训练后 3DGS 和渲染视角。输出：visual mesh。

## 在 Video2Mesh 中的位置

P1/P2 object visual mesh benchmark；raw mesh 较大，需要减面和清理。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
