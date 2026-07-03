---
title: Floater Cleaning
id: video2mesh-pointcloud-completion-floater-cleaning
category: 调研目录
visibility: public
summary: 先清理 3DGS/点云中的漂浮点和长尾离群点，能显著改善 mesh、截图和相机 framing。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# Floater Cleaning

## 简介

先清理 3DGS/点云中的漂浮点和长尾离群点，能显著改善 mesh、截图和相机 framing。

## 输入与输出

输入：point cloud 或 Gaussian PLY。输出：cleaned point cloud / cleaned Gaussian。

## 在 Video2Mesh 中的位置

P0 预处理，应放在 semantic transfer 和 mesh 重建前。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
