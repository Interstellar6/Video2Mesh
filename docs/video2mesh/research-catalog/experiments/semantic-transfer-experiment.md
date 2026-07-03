---
title: 语义投影融合实验
id: video2mesh-experiments-semantic-transfer-experiment
category: 调研目录
visibility: public
summary: 早期 P1 ray projection debug 尝试把语义投到 mesh face/点上。
tags:
  - 本项目实验
  - Research Catalog
---

# 语义投影融合实验

## 简介

早期 P1 ray projection debug 尝试把语义投到 mesh face/点上。

## 输入与输出

debug 图显示覆盖更高，但床、墙、窗帘、地面之间存在明显串色。

## 在 Video2Mesh 中的位置

保留路线，但需要真实 2D mask、深度可见性过滤和 smoothing。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
