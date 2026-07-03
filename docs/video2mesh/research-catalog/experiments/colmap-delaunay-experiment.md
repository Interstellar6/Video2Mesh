---
title: COLMAP Delaunay Dense 实验
id: video2mesh-experiments-colmap-delaunay-experiment
category: 调研目录
visibility: public
summary: COLMAP dense + Delaunay mesher 生成场景级 mesh。
tags:
  - 本项目实验
  - Research Catalog
---

# COLMAP Delaunay Dense 实验

## 简介

COLMAP dense + Delaunay mesher 生成场景级 mesh。

## 输入与输出

输出约 82,920 vertices / 167,082 triangles，GLB 约 3.0MB。

## 在 Video2Mesh 中的位置

当前最适合 P0 static collider。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
