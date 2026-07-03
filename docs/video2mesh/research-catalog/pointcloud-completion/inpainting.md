---
title: 2D/3D Inpainting
id: video2mesh-pointcloud-completion-inpainting
category: 调研目录
visibility: public
summary: 2D inpainting 可修复视图纹理，3D inpainting 可尝试补点或补 surface，但都需要语义和可见性约束。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# 2D/3D Inpainting

## 简介

2D inpainting 可修复视图纹理，3D inpainting 可尝试补点或补 surface，但都需要语义和可见性约束。

## 输入与输出

输入：masks、images、depth/point cloud。输出：修复图像、修复点云或补面。

## 在 Video2Mesh 中的位置

P1/P2，不应直接伪造物理可信 collider。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
