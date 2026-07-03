---
title: Rigid Body Interaction
id: video2mesh-object-simulation-rigid-body
category: 调研目录
visibility: public
summary: 刚体是物体交互第一步，要求 visual mesh、collider、mass、friction 和 body type 分离。
tags:
  - 物体仿真
  - Research Catalog
---

# Rigid Body Interaction

## 简介

刚体是物体交互第一步，要求 visual mesh、collider、mass、friction 和 body type 分离。

## 输入与输出

输入：object mesh/collider/physics metadata。输出：可移动或可碰撞物体。

## 在 Video2Mesh 中的位置

P1 首选。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
