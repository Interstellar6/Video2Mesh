---
title: Open3D Poisson
id: video2mesh-mesh-reconstruction-open3d-poisson
category: 调研目录
visibility: public
summary: Open3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。
tags:
  - Mesh 重建
  - Research Catalog
---

# Open3D Poisson

## 简介

Open3D Poisson 可以快速从点云和 normals 生成 watertight-ish mesh，是脚本化 baseline。

## 输入与输出

输入：带法线点云。输出：Poisson mesh。

## 在 Video2Mesh 中的位置

baseline/fallback。3DGS center point cloud 上容易生成壳状伪影。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
