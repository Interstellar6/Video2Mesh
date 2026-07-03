---
title: SuGaR
id: video2mesh-mesh-reconstruction-sugar
category: 调研目录
visibility: public
summary: SuGaR 将 Gaussians 对齐到表面，并从中提取可编辑 mesh，适合高质量 visual mesh 对照。
tags:
  - Mesh 重建
  - Research Catalog
---

# SuGaR

## 简介

SuGaR 将 Gaussians 对齐到表面，并从中提取可编辑 mesh，适合高质量 visual mesh 对照。

## 输入与输出

输入：3DGS 或训练数据。输出：surface-aligned Gaussians 和 mesh。

## 在 Video2Mesh 中的位置

P2 高质量 visual mesh 路线，环境和优化成本高。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
