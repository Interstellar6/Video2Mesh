---
title: Soft Body / Cloth
id: video2mesh-object-simulation-soft-body-cloth
category: 调研目录
visibility: public
summary: 窗帘、床品等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。
tags:
  - 物体仿真
  - Research Catalog
---

# Soft Body / Cloth

## 简介

窗帘、床品等软体需要特殊表示，普通 collider mesh 只能做视觉和粗碰撞。

## 输入与输出

输入：cloth mesh、constraints、material。输出：软体/布料仿真。

## 在 Video2Mesh 中的位置

P2，先用静态代理或简化面片。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
