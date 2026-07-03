---
title: CloudCompare / PoissonRecon
id: video2mesh-mesh-reconstruction-cloudcompare-poisson
category: 调研目录
visibility: public
summary: CloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。
tags:
  - Mesh 重建
  - Research Catalog
---

# CloudCompare / PoissonRecon

## 简介

CloudCompare 适合人工检查点云、估计法线、裁剪离群点，再调用 PoissonRecon 做传统建面。

## 输入与输出

输入：点云。输出：可视化检查结果和 Poisson mesh。

## 在 Video2Mesh 中的位置

人工诊断和方法对照，不建议直接作为无人值守主链路。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
