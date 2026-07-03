---
title: COLMAP
id: video2mesh-input-pose-pointcloud-colmap
category: 调研目录
visibility: public
summary: COLMAP 是当前 Video2Mesh 的 P0 位姿、稠密重建和 Delaunay mesh 基线。它提供相机参数、稀疏点、dense workspace 和可作为 collider 的传统几何。
tags:
  - 输入、位姿与点云
  - Research Catalog
---

# COLMAP

## 简介

COLMAP 是当前 Video2Mesh 的 P0 位姿、稠密重建和 Delaunay mesh 基线。它提供相机参数、稀疏点、dense workspace 和可作为 collider 的传统几何。

## 输入与输出

输入：多视角图像或视频抽帧。输出：相机、稠密点云、Delaunay/Poisson mesh。

## 在 Video2Mesh 中的位置

P0 主链路。它比 learned pose 方法更可控，也能直接接 mesh 和尺度检查。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
