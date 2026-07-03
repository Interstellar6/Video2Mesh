---
title: Primitive Fitting
id: video2mesh-collider-physics-proxy-primitive-fitting
category: 调研目录
visibility: public
summary: 对床、桌、柜、墙等物体拟合 box/plane/cylinder，可以得到更稳定的交互代理。
tags:
  - Collider 与物理代理
  - Research Catalog
---

# Primitive Fitting

## 简介

对床、桌、柜、墙等物体拟合 box/plane/cylinder，可以得到更稳定的交互代理。

## 输入与输出

输入：语义点云、bbox、mesh。输出：primitive collider。

## 在 Video2Mesh 中的位置

P1 object collider，适合刚体交互。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
