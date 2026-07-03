---
title: Rapier / Unity Physics
id: video2mesh-collider-physics-proxy-rapier-unity
category: 调研目录
visibility: public
summary: Rapier 适合 Web demo，Unity Physics/CharacterController 适合引擎集成。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Rapier / Unity Physics

## 简介

Rapier 适合 Web demo，Unity Physics/CharacterController 适合引擎集成。

## 输入与输出

输入：collider、body type、material。输出：runtime collision。

## 在 Video2Mesh 中的位置

P1 runtime 集成验证。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
