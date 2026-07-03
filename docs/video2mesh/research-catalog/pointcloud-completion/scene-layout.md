---
title: Scene Layout Completion
id: video2mesh-pointcloud-completion-scene-layout
category: 调研目录
visibility: public
summary: 场景结构补全关注墙、地、天花板、门窗、柜体等大结构，用于 collider 和导航边界。
tags:
  - 点云清理与背景补全
  - Research Catalog
---

# Scene Layout Completion

## 简介

场景结构补全关注墙、地、天花板、门窗、柜体等大结构，用于 collider 和导航边界。

## 输入与输出

输入：点云、语义、VLM/scene graph。输出：layout primitives 或结构 mesh。

## 在 Video2Mesh 中的位置

P1 物理代理补全，比视觉补纹理更重要。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
