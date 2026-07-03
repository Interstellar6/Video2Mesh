---
title: GraphDECO 3D Gaussian Splatting
id: video2mesh-visual-3dgs-graphdeco-3dgs
category: 调研目录
visibility: public
summary: GraphDECO 3DGS 是当前视觉层主线，负责从 posed images 训练高真实感 Gaussian 场景。
tags:
  - 视觉重建与 3DGS
  - Research Catalog
---

# GraphDECO 3D Gaussian Splatting

## 简介

GraphDECO 3DGS 是当前视觉层主线，负责从 posed images 训练高真实感 Gaussian 场景。

## 输入与输出

输入：COLMAP 相机和图像。输出：Gaussian PLY / point_cloud.ply 等 visual proxy。

## 在 Video2Mesh 中的位置

P0 visual layer。不要直接拿 Gaussian center 当 collider。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
