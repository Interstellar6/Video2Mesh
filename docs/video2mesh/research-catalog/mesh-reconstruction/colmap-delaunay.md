---
title: COLMAP Delaunay Mesher
id: video2mesh-mesh-reconstruction-colmap-delaunay
category: 调研目录
visibility: public
summary: COLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。
tags:
  - Mesh 重建
  - Research Catalog
---

# COLMAP Delaunay Mesher

## 简介

COLMAP dense + Delaunay mesher 能从传统 MVS workspace 生成比较稳定的场景 mesh。

## 输入与输出

输入：COLMAP dense workspace。输出：scene-level mesh。

## 在 Video2Mesh 中的位置

P0 scene collider 主路线，适合轻量静态碰撞代理。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
