---
title: Convex Decomposition
id: video2mesh-collider-physics-proxy-convex-decomposition
category: 调研目录
visibility: public
summary: V-HACD/CoACD 类方法把复杂 mesh 拆成凸体集合，利于物理引擎稳定求解。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Convex Decomposition

## 简介

V-HACD/CoACD 类方法把复杂 mesh 拆成凸体集合，利于物理引擎稳定求解。

## 输入与输出

输入：object mesh。输出：convex hull compound。

## 在 Video2Mesh 中的位置

P1 动态物体 collider。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
