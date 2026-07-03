---
title: Background Clean Plate
id: video2mesh-pointcloud-completion-background-clean-plate
category: 调研目录
visibility: public
summary: clean plate 是把移除物体后的背景补齐，World Labs / image-blaster 都体现了类似思想。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# Background Clean Plate

## 简介

clean plate 是把移除物体后的背景补齐，World Labs / image-blaster 都体现了类似思想。

## 输入与输出

输入：场景描述、移除物体 masks、背景参考。输出：修复背景或 static world。

## 在 Video2Mesh 中的位置

P1 背景补全，和 object mesh completion 分开。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
