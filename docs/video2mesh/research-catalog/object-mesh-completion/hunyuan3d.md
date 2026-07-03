---
title: Hunyuan3D
id: video2mesh-object-mesh-completion-hunyuan3d
category: 调研目录
visibility: public
summary: Hunyuan3D 适合从单图或少量参考生成物体 mesh，是 image-blaster 默认可接的 object backend 之一。
tags:
  - 物体 Mesh 补全
  - Research Catalog
---

# Hunyuan3D

## 简介

Hunyuan3D 适合从单图或少量参考生成物体 mesh，是 image-blaster 默认可接的 object backend 之一。

## 输入与输出

输入：物体 crop / reference image。输出：object-local mesh / GLB。

## 在 Video2Mesh 中的位置

P1 object visual completion，需要回填尺度和姿态。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
