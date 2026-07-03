---
title: Open3D Poisson 实验
id: video2mesh-experiments-open3d-poisson-experiment
category: 调研目录
visibility: public
summary: 使用过滤后的 3DGS center point cloud 做 Poisson baseline。
tags:
  - 本项目实验
  - Research Catalog
---

# Open3D Poisson 实验

## 简介

使用过滤后的 3DGS center point cloud 做 Poisson baseline。

## 输入与输出

alpha005_sample500k 输入 50 万点，输出约 100,965 vertices / 200,000 triangles，GLB 约 5.23MB。

## 在 Video2Mesh 中的位置

适合 fallback/debug，不适合最终 surface。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
