---
title: Spark / SuperSplat
id: video2mesh-visual-3dgs-spark-supersplat
category: 调研目录
visibility: public
summary: Spark 是浏览器端 splat 渲染路线，SuperSplat 适合检查和编辑 3DGS/Splat 资产。二者代表工业界 visual proxy 浏览器查看约定。
tags:
  - 视觉重建与 3DGS
  - Research Catalog
---

# Spark / SuperSplat

## 简介

Spark 是浏览器端 splat 渲染路线，SuperSplat 适合检查和编辑 3DGS/Splat 资产。二者代表工业界 visual proxy 浏览器查看约定。

## 输入与输出

输入：PLY/SPZ/SOG/SPLAT 等 splat 资产。输出：Web 可视化、检查、截图。

## 在 Video2Mesh 中的位置

Web 展示和 QA 工具，不负责 simulator bundle。

## 接入判断

- 是否进 P0：只在它能稳定提供当前闭环必需资产时进入。
- 是否进 P1：适合作为质量提升、物体级补全、语义增强或交互升级时进入。
- 是否保留为 P2/P3：当效果有潜力但工程成本、依赖、速度或开源状态不稳定时，先作为研究路线跟踪。
