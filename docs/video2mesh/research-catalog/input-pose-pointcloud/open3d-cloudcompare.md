---
title: Open3D / CloudCompare
id: video2mesh-input-pose-pointcloud-open3d-cloudcompare
category: 调研目录
visibility: public
summary: Open3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计和可视化对比。
tags:
  - 输入、位姿与点云
  - Research Catalog
---

# Open3D / CloudCompare

## 简介

Open3D 更适合脚本化点云处理和 Poisson/BPA baseline；CloudCompare 更适合人工检查、裁剪、法线估计和可视化对比。

## 输入与输出

输入：PLY/PCD/OBJ 等点云或 mesh。输出：清理点云、重建 mesh、诊断截图。

## 在 Video2Mesh 中的位置

debug 和 baseline 工具，不作为唯一生产算法。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
