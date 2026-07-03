---
title: InstantMesh
id: video2mesh-object-mesh-completion-instantmesh
category: 调研目录
visibility: public
summary: InstantMesh 是 feed-forward 图像到 mesh 路线，优势是速度和批量化。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# InstantMesh

## 简介

InstantMesh 是 feed-forward 图像到 mesh 路线，优势是速度和批量化。

## 输入与输出

输入：单图/多视角图像。输出：mesh。

## 在 Video2Mesh 中的位置

P1 批量候选，可能需要更多纹理和尺度修正。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
