---
title: Static Mesh Collider
id: video2mesh-collider-physics-proxy-static-mesh-collider
category: 调研目录
visibility: public
summary: 场景级 static mesh collider 用一个简化 mesh 承担地面、墙体、点击和粗碰撞。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Static Mesh Collider

## 简介

场景级 static mesh collider 用一个简化 mesh 承担地面、墙体、点击和粗碰撞。

## 输入与输出

输入：COLMAP Delaunay/Poisson mesh。输出：GLB collider。

## 在 Video2Mesh 中的位置

P0 必需，优先稳定和轻量。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
